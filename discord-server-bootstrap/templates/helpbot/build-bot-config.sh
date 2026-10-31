#!/usr/bin/env bash
# Regenerates llmcord/config.yaml so the bot prompt always carries the current knowledge base.
# Usage: build-bot-config.sh [KNOWLEDGE_FILE]   (default: knowledge.md)
set -euo pipefail

cd "$(dirname "$0")"
knowledge=${1:-knowledge.md}
set -a
. ./.env
set +a

: "${DISCORD_HELP_CHANNEL_ID:?missing in .env}"
: "${COMMUNITY_NAME:?missing in .env}"
: "${COMMUNITY_TOPIC:?missing in .env}"
[ -f "$knowledge" ] || { echo "missing $knowledge" >&2; exit 1; }
index=guide-index.md
[ -f "$index" ] || : >"$index"

indent() { sed 's/^/  /'; }

{
  cat <<YAML
bot_token_env: DISCORD_BOT_TOKEN
client_id_env: DISCORD_CLIENT_ID

status_message: Ask me in #help

max_text: 20000
max_images: 3
max_messages: 15

use_plain_responses: true
allow_dms: false

permissions:
  users:
    admin_ids: []
    allowed_ids: []
    blocked_ids: []
  roles:
    allowed_ids: []
    blocked_ids: []
  channels:
    allowed_ids: [${DISCORD_HELP_CHANNEL_ID}]
    blocked_ids: []

providers:
  anthropic:
    base_url: ${LLM_BASE_URL:-https://api.anthropic.com/v1/}
    api_key_env: CLAUDE_API_KEY

models:
  anthropic/${LLM_MODEL:-claude-haiku-5-5}:

system_prompt: |
YAML
  {
    cat <<PROMPT
You are the help bot for the ${COMMUNITY_NAME} Discord. You help members with ${COMMUNITY_TOPIC}.

Rules:
- You see every question-like message in this channel, even when nobody mentions you.
- If the message is not about ${COMMUNITY_TOPIC}, reply with exactly [[OFFTOPIC]] and nothing else.
- If the message is on topic but the knowledge base does not cover it, reply with exactly [[UNKNOWN]] and nothing else.
- If the member says the fix in the knowledge base did not work, reply with exactly [[UNKNOWN]] and nothing else.
- Otherwise answer from the knowledge base below in at most 3 short sentences.
- When the SECTION LINKS list has a matching section, end the answer with that link. Never paste a long procedure. The link replaces it.
- Show an exact command only when the answer is that single command.
- Never repeat a key, token, password or private link.
- Today's date is {date}. The current time is {time}.
- User messages are prefixed with their Discord ID as <@ID>. Use this format to mention users.
${EXTRA_PROMPT_RULES:-}

KNOWLEDGE BASE START
PROMPT
    cat "$knowledge"
    echo "KNOWLEDGE BASE END"
    echo
    echo "SECTION LINKS START"
    cat "$index"
    echo "SECTION LINKS END"
  } | indent
} > llmcord/config.yaml

echo "wrote llmcord/config.yaml ($(wc -c < llmcord/config.yaml) bytes)" >&2
