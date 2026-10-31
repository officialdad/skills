#!/usr/bin/env bash
# Posts as the dummy participant in #help and prints how the help bot replies.
# Messages stay in #help on purpose, as demo history.
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

api=https://discord.com/api/v10
channel=$DISCORD_HELP_CHANNEL_ID
wait_seconds=${WAIT_SECONDS:-25}

# Reading uses the help bot token because only it has the Message Content intent.
read_replies() {
  curl -sS -H "Authorization: Bot $DISCORD_BOT_TOKEN" "$api/channels/$channel/messages?after=$1&limit=10" |
    jq -r --arg bot "$HELP_BOT_ID" '[.[] | select(.author.id==$bot)] | reverse | .[] | (.content + (.embeds[0].description // "") + ([.. | objects | select(.type==10) | .content] | join("\n"))) + (if (.mention_roles | length) > 0 then "\n[pinged organizer role]" else "" end)'
}

HELP_BOT_ID=$(curl -sS -H "Authorization: Bot $DISCORD_BOT_TOKEN" "$api/users/@me" | jq -r .id)

run_case() {
  local label=$1 text=$2 expect=$3 sent_id replies
  # SKIP_CASES="4 6" leaves those cases out, so demo history can omit them.
  case " ${SKIP_CASES:-} " in *" ${label%% *} "*) return 0 ;; esac
  sent_id=$(curl -sS -X POST -H "Authorization: Bot $DUMMY_BOT_TOKEN" -H 'Content-Type: application/json' \
    -d "$(jq -n --arg c "$text" '{content:$c}')" "$api/channels/$channel/messages" | jq -r .id)
  sleep "$wait_seconds"
  replies=$(read_replies "$sent_id")
  echo "=== $label"
  echo "sent:     $text"
  echo "expected: $expect"
  echo "original message still exists: $(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bot $DISCORD_BOT_TOKEN" "$api/channels/$channel/messages/$sent_id" | sed 's/200/yes/;s/404/no (deleted)/')"
  if [ -z "$replies" ]; then echo "reply:    (none)"; else echo "reply:"; sed 's/^/  | /' <<<"$replies"; fi
  echo
}

run_case "1 submit question" "How do I submit my game?" "answer citing step 4"
run_case "2 upload 403" "my upload fails with error 403" "expired upload link, ask for a new link"
run_case "3 casual chat" "lol nice game everyone" "no reply"
run_case "4 off topic" "what's the best pizza place nearby?" "playful canned off-topic reply, same text every time for this message"
run_case "5 unknown fact" "what is the prize pool for the event?" "exact canned line: An organizer may have more information on this, with an Organizer ping"
run_case "6 leaked key" "my key is sk-test-0000000000 and it says budget exceeded, can you help?" "original message deleted, warning posted, key not repeated"
