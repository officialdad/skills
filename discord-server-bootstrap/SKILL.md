---
name: discord-server-bootstrap
description: Build a complete Discord server from a JSON spec using an Administrator bot token and the REST API, then run an LLM help bot (llmcord wrapper) in it. Use when the user wants to set up, rebuild or clone a Discord community server, add roles, channels, pins, onboarding, rules screening, invites, key claiming or team rooms, or deploy the help bot. Covers the env setup.
---

# Discord server bootstrap

An Administrator bot builds the server. The user does not click through Discord settings. The build is idempotent, so a rerun fixes drift and creates nothing twice.

## Inputs to collect

Ask only for what the repo and the user message do not give.

- Community name, topic, and the dates that matter.
- Whether any channel is a forum, and which posts it opens with.
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
| `channels[]` | `key`, `slug`, `name`, `type`, `access`, `topic`, `writers`, `private_roles`, `layout` (forums only) |
| `pins[]` | `channel`, `title` (bold first line, used to find the pin), `body`, optional `silent` (default false) |
| `first_posts[]` | A message posted only when the channel is empty. Optional `silent` (default false) |
| `forum_posts[]` | `channel` (a forum key), `title`, `body`, optional `pinned`, optional `silent` (default true) |
| `events[]` | Scheduled events with ISO 8601 times and an offset |
| `onboarding` | `default_channels` |
| `rules_screening` | `description`, `label`, `rules` |
| `invite_channel` | Optional. The channel key where the permanent invite lands. Omit it for a private server and no invite is made |
| `revoke_other_invites` | Optional, default false. Deletes every invite except the permanent one |

`roles` is optional. A server with no roles uses `public` channels only.

Placeholders in pin bodies: `{{channel:KEY}}` becomes a channel mention. `{{role:KEY}}` becomes a role mention.

### Channel types

`text`, `announcement`, `voice`, `stage`, `forum`.

A forum needs the Community feature. The build sets the forum to list layout (`"layout": "gallery"` switches it) and a 7 day auto-archive, so posts stay open between visits.

### Forum posts

- A post is matched by `title` inside its forum. A rerun creates nothing twice and edits the opening message when the text changed.
- Titles are at most 100 characters. Bodies are at most 2000 characters.
- `pinned` pins the post to the top of the forum. Discord allows one pinned post per forum.
- Posts are silent by default (message flag `SUPPRESS_NOTIFICATIONS`), so a bulk build pings nobody. Set `"silent": false` to notify.
- A forum lists newest activity first. The last post created shows on top, so order the array to suit.
- The build pauses 1 second after each new post and retries on a 429.
- Wrap a URL in `<...>` to hide its link preview.
- Pins and `first_posts` do not work in a forum. Use a pinned `forum_posts` entry.

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
- Listing invites needs Manage Server. If the call fails, the build warns and skips the invite step.
- The env file is written as soon as channel and role ids exist and again on exit, so a failed run keeps its ids. The write is atomic and never erases ids it does not know yet.
- The forum, forum post and no-invite paths ran against a live Community server with an Administrator bot. The onboarding, rules screening, events and permanent invite paths are older and less tested. Say which paths the first run on a new server leaves unconfirmed.

## Using the same bot in another server

Reuse the bot token and application. Invite the bot to the new server, set a new `DISCORD_GUILD_ID`, and run `bootstrap.sh` again to get new channel and role ids. Run one container per server. See `references/env.md`.

## References

- `references/env.md` - every env variable and its source.
- `references/helpbot.md` - bot setup, layout, run order, features.
- `references/lessons.md` - Discord, discord.py and llmcord gotchas.
- `references/checklist.md` - verification list.
