# Env reference

Keep the file `.env` at mode 600. Never print values. Mask them when you inspect the file.

## Set by the user

| Variable | Needed | Where it comes from |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Always | Developer Portal > Bot > Reset Token |
| `DISCORD_GUILD_ID` | Always | Discord Settings > Advanced > Developer Mode, then right-click the server > Copy Server ID |
| `DISCORD_CLIENT_ID` | Help bot | Developer Portal > General Information > Application ID |
| `CLAUDE_API_KEY` | Help bot | An Anthropic API key. The variable name stays `CLAUDE_API_KEY` because the config builder reads it |
| `COMMUNITY_NAME` | Help bot | Plain name, for example `Acme Builders` |
| `COMMUNITY_TOPIC` | Help bot | What the bot answers about, for example `building and publishing games` |
| `LLM_MODEL` | Optional | Default `claude-haiku-5-5` |
| `LLM_BASE_URL` | Optional | Default `https://api.anthropic.com/v1/` |
| `EXTRA_PROMPT_RULES` | Optional | Extra lines for the bot prompt, one rule per line starting with `- ` |
| `DUMMY_BOT_TOKEN` | Optional | A second bot used only to test the help bot as a fake member |
| `TEST_BOT_IDS` | Optional | The dummy bot's user id. Remove both test variables before launch if you do not need them |

## Written by `bootstrap.sh`

The builder replaces these on every run. Never edit them by hand.

| Variable | Meaning |
|---|---|
| `DISCORD_<KEY>_CHANNEL_ID` | One per channel in the spec. `<KEY>` is the channel `key`, upper case, with `-` as `_` |
| `DISCORD_<KEY>_ROLE_ID` | One per role in the spec |
| `DISCORD_INVITE_URL` | The permanent invite |

## Switches the help bot reads

A feature turns on when its variable has a value. It stays off when the variable is empty or missing.

| Variable | Turns on |
|---|---|
| `DISCORD_HELP_CHANNEL_ID` | The question and answer channel. Required |
| `DISCORD_ORGANIZER_ROLE_ID` | Organizer-only commands and the unknown-answer ping. Required |
| `DISCORD_GETKEY_CHANNEL_ID` | The `/getkey` and `/reset-key` commands and the typed-text cleanup in that channel |
| `DISCORD_MEMBER_ROLE_ID` | The role granted after a successful `/getkey`. Needs `GETKEY` |
| `DISCORD_TEAM_FINDER_CHANNEL_ID` | The team button and the `/team` commands |

The channel and role keys in the spec decide the variable names. A spec channel with `key: getkey` writes `DISCORD_GETKEY_CHANNEL_ID`. A spec role with `key: member` writes `DISCORD_MEMBER_ROLE_ID`. A spec role with `key: organizer` writes `DISCORD_ORGANIZER_ROLE_ID`. Use those exact keys for the help bot.

## Same bot, another server

Reuse the same application, bot token and client id. Do not create a new bot.

| Item | Action |
|---|---|
| Bot token | Reuse. One token works in every server the bot joined |
| Application and client id | Reuse |
| Invite the bot | Create the invite URL again with `guild_id` unset and open it as an owner or admin of the new server |
| `DISCORD_GUILD_ID` | Change. It names the new server |
| Channel and role ids | Regenerate. Run `bootstrap.sh` against the new server. Every id is different |
| Bot role position | Move the bot role above the roles it assigns, on the new server |
| Slash commands | Global commands appear in every server. Guild-only checks in the code limit them |
| Running the bot | One running container serves all servers, but it reads one set of channel ids. To serve two servers with different channels, run two containers with two env files |
| Claims and teams data | Separate `data/` directory per container, or the ids collide |
| Privileged intent | Message Content is a per-application switch. It stays on |
| Verification | Past 100 servers, Discord asks to verify the bot. Bot privileged intents need approval then |

Use one bot for one server at a time in practice. Two servers with the same env file would make the bot answer in channel ids that do not exist in the second one.
