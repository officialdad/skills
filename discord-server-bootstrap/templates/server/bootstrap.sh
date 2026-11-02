#!/usr/bin/env bash
# Builds a Discord server from a JSON spec with an Administrator bot. Safe to rerun.
# Usage: bootstrap.sh [--check-spec] SPEC.json [ENV_FILE]
set -euo pipefail

check_only=0
if [ "${1:-}" = "--check-spec" ]; then check_only=1; shift; fi
spec=${1:?usage: bootstrap.sh [--check-spec] SPEC.json [ENV_FILE]}
env_file=${2:-.env}

PERM_BITS='{"VIEW":1024,"SEND":2048,"MANAGE_MESSAGES":8192,"HISTORY":65536,"REACT":64,"EMBED":16384,"ATTACH":32768,"MENTION_EVERYONE":131072,"MANAGE_CHANNELS":16,"CONNECT":1048576,"SPEAK":2097152,"MUTE_MEMBERS":4194304,"MOVE_MEMBERS":16777216,"USE_APP_COMMANDS":2147483648,"MANAGE_EVENTS":8589934592,"THREADS_CREATE":34359738368,"THREADS_SEND":274877906944}'

check_spec() {
  jq -e --argjson bits "$PERM_BITS" '
    def dup(a): (a | group_by(.) | map(select(length > 1)) | flatten);
    ([.categories[].channels[].key]) as $ck
    | ([.categories[].channels[] | select(.type == "forum") | .key]) as $fk
    | ([(.roles // [])[].key]) as $rk
    | ($bits | keys) as $valid
    | {
        duplicate_channel_keys: dup($ck),
        duplicate_role_keys: dup($rk),
        unknown_roles: [.categories[].channels[] | ((.private_roles // []) + (.writers // []))[] | select(. as $r | $rk | index($r) | not)],
        unknown_permissions: [(.roles // [])[].perms[] | select(. as $p | $valid | index($p) | not)],
        bad_access: [.categories[].channels[] | select(.access as $a | ["public","read_only","slash_only","private"] | index($a) | not) | .key],
        bad_type: [.categories[].channels[] | select(.type as $t | ["text","announcement","voice","stage","forum"] | index($t) | not) | .key],
        unknown_pin_channels: [(.pins // [])[] | .channel | select(. as $c | $ck | index($c) | not)],
        unknown_invite_channel: [(.invite_channel // empty) | select(. as $c | $ck | index($c) | not)],
        bad_layout: [.categories[].channels[] | select(.layout != null and (.layout | IN("list","gallery") | not)) | .key],
        unknown_forum_post_channels: [(.forum_posts // [])[] | .channel | select(. as $c | $fk | index($c) | not)],
        duplicate_forum_post_titles: dup([(.forum_posts // [])[] | "\(.channel)/\(.title)"]),
        bad_forum_post_title: [(.forum_posts // [])[] | select((.title | length) == 0 or (.title | length) > 100) | .title],
        forum_post_body_too_long: [(.forum_posts // [])[] | select((.body | length) > 2000) | .title],
        forums_with_two_pinned_posts: [(.forum_posts // []) | group_by(.channel)[] | select(map(select(.pinned == true)) | length > 1) | .[0].channel],
        pins_or_first_posts_in_forum: [((.pins // [])[], (.first_posts // [])[]) | .channel | select(. as $c | $fk | index($c))],
        unknown_default_channels: [(.onboarding.default_channels // [])[] | select(. as $c | $ck | index($c) | not)]
      }
    | to_entries | map(select(.value | length > 0))
    | if length == 0 then true else (map("\(.key): \(.value | join(", "))") | join("\n") | halt_error(1)) end
  ' "$spec" >/dev/null
}

check_spec
echo "spec ok" >&2
[ "$check_only" = 1 ] && exit 0

set -a
# shellcheck disable=SC1090
. "$env_file"
set +a
: "${DISCORD_BOT_TOKEN:?missing in env file}"
: "${DISCORD_GUILD_ID:?missing in env file}"

api=https://discord.com/api/v10
guild=$DISCORD_GUILD_ID

call() {
  local method=$1 path=$2 body=${3:-} out status
  while :; do
    if [ -n "$body" ]; then
      out=$(curl -sS -w '\n%{http_code}' -X "$method" -H "Authorization: Bot $DISCORD_BOT_TOKEN" -H 'Content-Type: application/json' -d "$body" "$api$path")
    else
      out=$(curl -sS -w '\n%{http_code}' -X "$method" -H "Authorization: Bot $DISCORD_BOT_TOKEN" "$api$path")
    fi
    status=${out##*$'\n'}
    out=${out%$'\n'*}
    if [ "$status" = 429 ]; then sleep "$(jq -r '.retry_after // 2' <<<"$out")"; continue; fi
    if [ "$status" -ge 400 ]; then echo "Discord API error $status on $method $path: $out" >&2; return 1; fi
    printf '%s' "$out"
    return 0
  done
}

bits() { jq -n --argjson m "$PERM_BITS" --argjson n "$1" '[$n[] | $m[.]] | add // 0'; }
ow() { jq -n --arg id "$1" --arg t "$2" --arg allow "$3" --arg deny "$4" '{id:$id,type:($t|tonumber),allow:$allow,deny:$deny}'; }
var_name() { printf 'DISCORD_%s_%s_ID' "$(tr 'a-z-' 'A-Z_' <<<"$1")" "$2"; }
hex_to_int() { printf '%d' "0x${1#\#}"; }
# Message flag 4096 posts without a notification, so a bulk build pings nobody.
silent_flag() { jq -n --argjson s "$1" 'if $s then 4096 else 0 end'; }

bot_id=$(call GET /users/@me | jq -r .id)
roles=$(call GET "/guilds/$guild/roles")
channels=$(call GET "/guilds/$guild/channels")

declare -A role_id channel_id

# Merges the ids known so far into the env file. A key not known yet keeps its old line, so a partial run never erases ids.
# The temp file sits next to the env file so the final mv is one atomic rename.
write_ids() {
  local tmp key known=()
  [ "${#channel_id[@]}" -gt 0 ] || [ "${#role_id[@]}" -gt 0 ] || return 0
  tmp=$(mktemp "$env_file.XXXXXX")
  for key in "${!channel_id[@]}"; do known+=("$(var_name "$key" CHANNEL)"); done
  for key in "${!role_id[@]}"; do known+=("$(var_name "$key" ROLE)"); done
  [ -z "$code" ] || known+=(DISCORD_INVITE_URL)
  grep -vE "^($(IFS='|'; echo "${known[*]}"))=" "$env_file" >"$tmp" || true
  {
    for key in "${!channel_id[@]}"; do echo "$(var_name "$key" CHANNEL)=${channel_id[$key]}"; done
    for key in "${!role_id[@]}"; do echo "$(var_name "$key" ROLE)=${role_id[$key]}"; done
    [ -z "$code" ] || echo "DISCORD_INVITE_URL=https://discord.gg/$code"
  } >>"$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$env_file"
}
code=''
trap 'write_ids' EXIT

# Roles are matched by name. Reruns update color and permissions in place.
while read -r role; do
  key=$(jq -r .key <<<"$role"); name=$(jq -r .name <<<"$role")
  body=$(jq -n --argjson r "$role" --arg p "$(bits "$(jq -c .perms <<<"$role")")" --argjson c "$(hex_to_int "$(jq -r .color <<<"$role")")" \
    '{name:$r.name,color:$c,permissions:$p,hoist:($r.hoist // false),mentionable:($r.mentionable // false)}')
  id=$(jq -r --arg n "$name" '.[] | select(.name==$n) | .id' <<<"$roles" | head -n1)
  if [ -z "$id" ]; then
    id=$(call POST "/guilds/$guild/roles" "$body" | jq -r .id); echo "created role $name" >&2
  else
    call PATCH "/guilds/$guild/roles/$id" "$body" >/dev/null
  fi
  role_id[$key]=$id
done < <(jq -c '(.roles // [])[]' "$spec")

# Channel names are "<emoji>｜<slug>". Matching on the slug keeps reruns safe when the emoji changes.
find_channel() {
  jq -r --arg s "$1" '.[] | select((.type==0 or .type==2 or .type==5 or .type==13 or .type==15) and (.name==$s or (.name|endswith("｜"+$s)))) | .id' <<<"$channels" | head -n1
}

bot_allow=$(bits '["VIEW","SEND","HISTORY","MANAGE_MESSAGES","THREADS_CREATE","THREADS_SEND","EMBED","ATTACH"]')
voice_admin='["VIEW","CONNECT","SPEAK","MANAGE_CHANNELS","MUTE_MEMBERS","MOVE_MEMBERS"]'

overwrites_for() {
  local channel=$1 access type parts=() r
  access=$(jq -r .access <<<"$channel"); type=$(jq -r .type <<<"$channel")
  case $access in
    public)
      if [ "$type" = voice ] || [ "$type" = stage ]; then parts+=("$(ow "$guild" 0 "$(bits '["VIEW","CONNECT","SPEAK"]')" 0)")
      else parts+=("$(ow "$guild" 0 "$(bits '["VIEW","SEND","HISTORY","REACT","EMBED","ATTACH","THREADS_CREATE","THREADS_SEND"]')" 0)"); fi ;;
    read_only)
      parts+=("$(ow "$guild" 0 "$(bits '["VIEW","HISTORY"]')" "$(bits '["SEND"]')")")
      for r in $(jq -r '.writers // [] | .[]' <<<"$channel"); do parts+=("$(ow "${role_id[$r]}" 0 "$(bits '["SEND"]')" 0)"); done
      parts+=("$(ow "$bot_id" 1 "$bot_allow" 0)") ;;
    slash_only)
      # Discord disables the message box without SEND, which blocks typing a slash command. The bot deletes typed text instead.
      parts+=("$(ow "$guild" 0 "$(bits '["VIEW","HISTORY","SEND","USE_APP_COMMANDS"]')" "$(bits '["THREADS_CREATE","ATTACH","EMBED"]')")")
      parts+=("$(ow "$bot_id" 1 "$bot_allow" 0)") ;;
    private)
      parts+=("$(ow "$guild" 0 0 "$(bits '["VIEW"]')")")
      for r in $(jq -r '.private_roles // [] | .[]' <<<"$channel"); do
        if [ "$type" = voice ] || [ "$type" = stage ]; then parts+=("$(ow "${role_id[$r]}" 0 "$(bits "$voice_admin")" 0)")
        else parts+=("$(ow "${role_id[$r]}" 0 "$(bits '["VIEW","SEND","HISTORY"]')" 0)"); fi
      done
      parts+=("$(ow "$bot_id" 1 "$bot_allow" 0)") ;;
  esac
  printf '%s\n' "${parts[@]}" | jq -s .
}

type_code() { case $1 in text) echo 0 ;; voice) echo 2 ;; announcement) echo 5 ;; stage) echo 13 ;; forum) echo 15 ;; esac; }

order='[]'
while read -r category; do
  match=$(jq -r '.match // .name' <<<"$category"); name=$(jq -r .name <<<"$category")
  cat_id=$(jq -r --arg k "$match" '.[] | select(.type==4 and (.name|contains($k))) | .id' <<<"$channels" | head -n1)
  if [ -z "$cat_id" ]; then
    cat_id=$(call POST "/guilds/$guild/channels" "$(jq -n --arg n "$name" '{name:$n,type:4}')" | jq -r .id); echo "created category $name" >&2
  else
    call PATCH "/channels/$cat_id" "$(jq -n --arg n "$name" '{name:$n}')" >/dev/null
  fi
  order=$(jq -c --arg id "$cat_id" '. + [[$id,""]]' <<<"$order")

  while read -r channel; do
    key=$(jq -r .key <<<"$channel"); display=$(jq -r .name <<<"$channel"); type=$(jq -r .type <<<"$channel")
    id=$(find_channel "$(jq -r .slug <<<"$channel")")
    body=$(jq -n --argjson c "$channel" --argjson ty "$(type_code "$type")" --arg p "$cat_id" --argjson o "$(overwrites_for "$channel")" \
      '{name:$c.name,type:$ty,parent_id:$p,permission_overwrites:$o}
       + (if ($c.type=="voice" or $c.type=="stage") then {} else {topic:($c.topic // "")} end)
       + (if $c.type=="forum" then {default_auto_archive_duration:10080,default_forum_layout:(if $c.layout=="gallery" then 2 else 1 end)} else {} end)')
    if [ -z "$id" ]; then
      id=$(call POST "/guilds/$guild/channels" "$body" | jq -r .id); echo "created channel $display" >&2
    else
      # Voice, stage and forum channels reject a type change, and their type never changes here.
      case $type in voice|stage|forum) body=$(jq -c 'del(.type)' <<<"$body") ;; esac
      call PATCH "/channels/$id" "$body" >/dev/null; echo "updated channel $display" >&2
    fi
    channel_id[$key]=$id
    order=$(jq -c --arg id "$id" --arg p "$cat_id" '. + [[$id,$p]]' <<<"$order")
  done < <(jq -c '.channels[]' <<<"$category")
done < <(jq -c '.categories[]' "$spec")

# The bulk reorder call accepts one parent change at a time, so it sends positions only.
call PATCH "/guilds/$guild/channels" "$(jq -c 'to_entries | map({id:.value[0],position:.key})' <<<"$order")" >/dev/null
echo "ordered channels" >&2

resolve() {
  local text=$1 key
  for key in "${!channel_id[@]}"; do text=${text//"{{channel:$key}}"/"<#${channel_id[$key]}>"}; done
  for key in "${!role_id[@]}"; do text=${text//"{{role:$key}}"/"<@&${role_id[$key]}>"}; done
  printf '%s' "$text"
}

# A pin is found by its bold title, so no marker text shows to readers.
while read -r pin; do
  channel=${channel_id[$(jq -r .channel <<<"$pin")]}; title=$(jq -r .title <<<"$pin")
  content=$(resolve "$title"$'\n\n'"$(jq -r .body <<<"$pin")")
  id=$(call GET "/channels/$channel/pins" | jq -r --arg t "$title" '[.[] | select(.content | startswith($t))][0].id // empty')
  if [ -n "$id" ]; then
    call PATCH "/channels/$channel/messages/$id" "$(jq -n --arg c "$content" '{content:$c}')" >/dev/null
  else
    id=$(call POST "/channels/$channel/messages" "$(jq -n --arg c "$content" --argjson f "$(silent_flag "$(jq '.silent // false' <<<"$pin")")" '{content:$c,flags:$f}')" | jq -r .id)
    call PUT "/channels/$channel/pins/$id" >/dev/null
  fi
  echo "pinned $title" >&2
done < <(jq -c '(.pins // [])[]' "$spec")

# Posted once. The channel is checked first so reruns never repeat it.
while read -r post; do
  channel=${channel_id[$(jq -r .channel <<<"$post")]}
  if [ "$(call GET "/channels/$channel/messages?limit=1" | jq length)" = 0 ]; then
    call POST "/channels/$channel/messages" "$(jq -n --arg c "$(resolve "$(jq -r .body <<<"$post")")" --argjson f "$(silent_flag "$(jq '.silent // false' <<<"$post")")" '{content:$c,flags:$f,allowed_mentions:{parse:[]}}')" >/dev/null
    echo "posted first message" >&2
  fi
done < <(jq -c '(.first_posts // [])[]' "$spec")

# Forum posts are matched by title inside their forum. A rerun edits the opening message when the text drifted and never posts twice.
# Posts are silent unless the spec sets "silent": false, so a bulk build pings nobody. A forum lists newest first, so the last post created shows on top.
if jq -e '(.forum_posts // []) | length > 0' "$spec" >/dev/null; then
  active_threads=$(call GET "/guilds/$guild/threads/active")
  declare -A forum_threads
  while read -r post; do
    key=$(jq -r .channel <<<"$post"); forum=${channel_id[$key]}; title=$(jq -r .title <<<"$post")
    if [ -z "${forum_threads[$key]:-}" ]; then
      archived='[]'; before=''
      while :; do
        page=$(call GET "/channels/$forum/threads/archived/public?limit=100${before:+&before=$before}")
        archived=$(jq -c --argjson p "$page" '. + $p.threads' <<<"$archived")
        [ "$(jq -r .has_more <<<"$page")" = true ] || break
        before=$(jq -rn --arg t "$(jq -r '.threads[-1].thread_metadata.archive_timestamp' <<<"$page")" '$t | @uri')
      done
      forum_threads[$key]=$(jq -c --arg f "$forum" --argjson a "$archived" '[.threads[] | select(.parent_id==$f)] + $a' <<<"$active_threads")
    fi
    content=$(resolve "$(jq -r .body <<<"$post")")
    thread=$(jq -c --arg t "$title" '[.[] | select(.name==$t)][0] // empty' <<<"${forum_threads[$key]}")
    if [ -z "$thread" ]; then
      thread=$(call POST "/channels/$forum/threads" "$(jq -n --arg n "$title" --arg c "$content" --argjson f "$(silent_flag "$(jq '.silent // true' <<<"$post")")" \
        '{name:$n,message:{content:$c,flags:$f,allowed_mentions:{parse:[]}}}')")
      echo "created forum post $title" >&2
      sleep 1
    else
      id=$(jq -r .id <<<"$thread")
      if [ "$(call GET "/channels/$id/messages/$id" | jq -r .content)" != "$content" ]; then
        # Discord rejects an edit inside an archived post.
        [ "$(jq -r .thread_metadata.archived <<<"$thread")" = true ] && call PATCH "/channels/$id" '{"archived":false}' >/dev/null
        call PATCH "/channels/$id/messages/$id" "$(jq -n --arg c "$content" '{content:$c}')" >/dev/null
        echo "updated forum post $title" >&2
      fi
    fi
    if [ "$(jq -r '.pinned // false' <<<"$post")" = true ] && [ "$(jq -r '((.flags // 0) / 2 | floor) % 2' <<<"$thread")" != 1 ]; then
      call PATCH "/channels/$(jq -r .id <<<"$thread")" "$(jq -nc --argjson f "$(jq -r '(.flags // 0) + 2' <<<"$thread")" '{flags:$f}')" >/dev/null
      echo "pinned forum post $title" >&2
    fi
  done < <(jq -c '.forum_posts[]' "$spec")
fi

events=$(call GET "/guilds/$guild/scheduled-events")
while read -r event; do
  name=$(jq -r .name <<<"$event")
  body=$(jq -n --argjson e "$event" '{name:$e.name,description:($e.description // ""),scheduled_start_time:$e.start,scheduled_end_time:$e.end,privacy_level:2,entity_type:3,entity_metadata:{location:$e.location}}')
  id=$(jq -r --arg n "$name" '.[] | select(.name==$n) | .id' <<<"$events" | head -n1)
  if [ -z "$id" ]; then call POST "/guilds/$guild/scheduled-events" "$body" >/dev/null; echo "created event $name" >&2
  else call PATCH "/guilds/$guild/scheduled-events/$id" "$body" >/dev/null; echo "updated event $name" >&2; fi
done < <(jq -c '(.events // [])[]' "$spec")
stale=$(jq -r --arg b "$bot_id" --argjson keep "$(jq -c '[(.events // [])[].name]' "$spec")" \
  '.[] | select(.creator_id==$b and ((.name as $n | $keep | index($n)) | not)) | .id' <<<"$events")
for id in $stale; do call DELETE "/guilds/$guild/scheduled-events/$id" >/dev/null; echo "removed stale event $id" >&2; done

# Only fills an empty description, so one edited by hand survives reruns. The banner needs boost level 2 and is not set here.
description=$(jq -r '.description // empty' "$spec")
if [ -n "$description" ] && [ -z "$(call GET "/guilds/$guild" | jq -r '.description // empty')" ]; then
  call PATCH "/guilds/$guild" "$(jq -n --arg d "$description" '{description:$d}')" >/dev/null; echo "set server description" >&2
fi

if jq -e '.onboarding' "$spec" >/dev/null; then
  defaults=$(jq -c --argjson ids "$(for k in "${!channel_id[@]}"; do jq -n --arg k "$k" --arg v "${channel_id[$k]}" '{($k):$v}'; done | jq -s add)" \
    '[.onboarding.default_channels[] | $ids[.]]' "$spec")
  call PUT "/guilds/$guild/onboarding" "$(jq -n --argjson d "$defaults" '{enabled:true,mode:0,default_channel_ids:$d,prompts:[]}')" >/dev/null && echo "onboarding on" >&2 \
    || echo "warning: onboarding needs the Community feature. Enable it in Server Settings, then rerun." >&2
fi

# The rules screening endpoint takes PATCH, not PUT.
if jq -e '.rules_screening' "$spec" >/dev/null; then
  call PATCH "/guilds/$guild/member-verification" "$(jq '{enabled:true,description:.rules_screening.description,form_fields:[{field_type:"TERMS",label:.rules_screening.label,required:true,values:.rules_screening.rules}]}' "$spec")" >/dev/null \
    && echo "rules screening on" >&2 || echo "warning: rules screening needs the Community feature" >&2
fi

# Optional. One permanent invite that lands in the channel with the welcome pin. Without invite_channel no invite is made or listed.
# Listing invites needs Manage Server. Without it the invite step is skipped, because creating blind would add an invite on every rerun.
code=''
invite_key=$(jq -r '.invite_channel // empty' "$spec")
revoke=$(jq -r '.revoke_other_invites // false' "$spec")
if [ -n "$invite_key" ] || [ "$revoke" = true ]; then
  if invites=$(call GET "/guilds/$guild/invites"); then
    if [ -n "$invite_key" ]; then
      invite_channel=${channel_id[$invite_key]}
      code=$(jq -r --arg b "$bot_id" --arg c "$invite_channel" '[.[] | select(.inviter.id==$b and .max_age==0 and .max_uses==0 and .channel.id==$c)][0].code // empty' <<<"$invites")
      if [ -z "$code" ]; then
        code=$(call POST "/channels/$invite_channel/invites" '{"max_age":0,"max_uses":0,"unique":true}' | jq -r .code); echo "created permanent invite" >&2
      fi
    fi
    if [ "$revoke" = true ]; then
      for other in $(jq -r --arg k "$code" '.[] | select(.code != $k) | .code' <<<"$invites"); do call DELETE "/invites/$other" >/dev/null; echo "deleted invite $other" >&2; done
    fi
  else
    echo "warning: cannot list invites. The bot needs Manage Server. Skipped the invite step." >&2
  fi
fi

write_ids
trap - EXIT
echo "done. IDs written to $env_file.${code:+ Invite: https://discord.gg/$code}" >&2
