---
name: discord-server-bootstrap
description: Build a complete Discord server from a JSON spec using an Administrator bot token and the REST API, then run an LLM help bot (llmcord wrapper) in it. Use when the user wants to set up, rebuild or clone a Discord community server, add roles, channels, pins, onboarding, rules screening, invites, key claiming or team rooms, or deploy the help bot. Covers the env setup.
---

# Discord server bootstrap

An Administrator bot builds the server. The user does not click through Discord settings. The build is idempotent, so a rerun fixes drift and creates nothing twice.

## Inputs to collect

Ask only for what the repo and the user message do not give.

- Community name, topic, and the dates that matter.
- Roles, and who can write where.
- Channel list, grouped in categories.
- Whether the help bot, key claiming and teams are wanted.
- The knowledge the bot answers from.

## Workflow

1. Create a project directory. Copy `templates/env.example` to `.env` and run `chmod 600 .env`.
2. Walk the user through the bot setup in `references/helpbot.md` (Developer Portal, intents, invite with `permissions=8`). The user must do this part. It needs their login.
3. Ask the user to fill `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID`. Never print them.
4. Copy `templates/server/server-spec.example.json` to `spec.json`. Edit it to match the community.
5. Run `templates/server/bootstrap.sh --check-spec spec.json`. Fix every reported error.
6. Run `templates/server/bootstrap.sh spec.json .env`. Read the output.
7. Run it again. A clean second run is the idempotency check.
8. For the help bot, follow `references/helpbot.md`. Copy the templates, write `knowledge.md`, run `build-bot-config.sh`, run `docker compose up -d --build`.
9. Run the items in `references/checklist.md`. State which items a human must test.

## Spec format

The example in `templates/server/server-spec.example.json` shows every field.

| Field | Meaning |
|---|---|
| `roles[]` | `key`, `name`, `color`, `hoist`, `mentionable`, `perms` (permission names) |
| `categories[]` | `key`, `name`, `match` (a substring that finds an existing category), `channels[]` |
| `channels[]` | `key`, `slug`, `name`, `type`, `access`, `topic`, `writers`, `private_roles` |
| `pins[]` | `channel`, `title` (bold first line, used to find the pin), `body` |
| `first_posts[]` | A message posted only when the channel is empty |
| `events[]` | Scheduled events with ISO 8601 times and an offset |
| `onboarding` | `default_channels` |
| `rules_screening` | `description`, `label`, `rules` |
| `invite_channel` | The channel key where the permanent invite lands |

Placeholders in pin bodies: `{{channel:KEY}}` becomes a channel mention. `{{role:KEY}}` becomes a role mention.

### Channel types

`text`, `announcement`, `voice`, `stage`.

### Access modes

| Mode | Members can | Use for |
|---|---|---|
| `public` | Read and write | Chat and help channels |
| `read_only` | Read only. `writers` roles can write | Rules and announcements |
| `slash_only` | Read and run slash commands. Typed text is deleted by the bot | A key claim channel |
| `private` | Nothing. Only `private_roles` see it | Organizer channels |

`slash_only` allows Send Messages, because Discord disables the message box without it. The help bot removes typed text.

## Rules

- Match channels by `slug`, never by position or emoji. This keeps reruns safe.
- Match pins by their bold title. Never add a visible marker.
- Set the server description only when empty.
- Never print a token or key. Mask values when you show `.env`.
- Never write secrets to the spec, the knowledge file or the bot prompt.
- Revoke other invites only when `revoke_other_invites` is true, and tell the user the count first.
- The build has not run against a live server in this skill's test pass. Only `--check-spec` and a syntax check ran. Run the first build on a throwaway server, or tell the user the first run is unconfirmed.

## Using the same bot in another server

Reuse the bot token and application. Invite the bot to the new server, set a new `DISCORD_GUILD_ID`, and run `bootstrap.sh` again to get new channel and role ids. Run one container per server. See `references/env.md`.

## References

- `references/env.md` - every env variable and its source.
- `references/helpbot.md` - bot setup, layout, run order, features.
- `references/lessons.md` - Discord, discord.py and llmcord gotchas.
- `references/checklist.md` - verification list.
