# Lessons from the first build

Each item cost time once. Read this before you debug.

## Discord API

- **Bulk reorder:** `PATCH /guilds/{id}/channels` takes one parent change at a time. Send `{id, position}` only.
- **Rules screening:** the endpoint `/guilds/{id}/member-verification` takes `PATCH`. `PUT` returns 405.
- **Onboarding:** `PUT /guilds/{id}/onboarding` works with a bot token that has Administrator. It needs the Community feature.
- **Slash command typing:** Discord disables the message box in a channel where `@everyone` lacks Send Messages. A read-only channel therefore blocks typing a slash command. Allow Send Messages there and let the bot delete typed text.
- **Voice and stage channels:** they reject a topic and a type change on update.
- **Server description:** the limit is 120 characters. Set it only when empty, so a hand edit survives reruns.
- **Banner:** needs boost level 2. Do not try it on a new server.
- **Role colors on managed bot roles:** the API ignores a color change. Change it by hand in Server Settings > Roles.
- **Raid detection:** a burst of joins turns on a DM pause for about two hours. It does not stop invites, chat or voice. The bot's ephemeral replies are unaffected.
- **Pins:** find a pin by its bold first line. A hidden marker such as `[jam-welcome]` shows to readers.
- **Mentions:** roles ping only in plain message content. An embed does not ping. Pass `allowed_mentions` with the exact users or roles.
- **Timestamps:** write `<t:UNIX:f> (<t:UNIX:R>)` for a deadline. It shows in each reader's own time zone with a live countdown.
- **Invites:** create one permanent invite that lands in the channel holding the welcome pin. Delete every other invite.

## discord.py

- **Modal user picker:** `discord.ui.Label` with `discord.ui.UserSelect` works in 2.7.1. Check with `hasattr(discord.ui, "Label")` on the installed version.
- **Persistent button:** register the view once with `bot.add_view` after the loop runs. `on_ready` fires again after a reconnect.
- **Message content:** the intent must be on in the Developer Portal and in code, or the bot reads empty messages.
- **Bots cannot click buttons or run slash commands.** A bot test cannot cover them. State plainly what a human must test.

## llmcord

- The wrapper pattern leaves `llmcord.py` unmodified. A small `run.py` imports it, patches `asyncio.run` to register commands, and wraps `on_message`.
- llmcord drops every bot author. A test bot id in `TEST_BOT_IDS` is flipped to human inside the wrapper so the real path runs.
- Replies come as components, so `content` is empty in the API. Read `type==10` components for the text.
- `use_plain_responses: true` is needed for role pings.
- The bot skips unprompted replies to organizers. An explicit mention bypasses the skip. Test with a second account or a mention.
- `docker compose restart` does not reload `.env`. Use `docker compose up -d --force-recreate`.

## Process

- Check the audit log before you blame the bot. Another admin may have created invites or changed settings.
- Read replies back from the channel after a test. A listing right after a bulk delete can be stale for a few seconds.
- Run the e2e test in the background. It takes about two minutes.
