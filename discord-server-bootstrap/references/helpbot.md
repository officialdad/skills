# Help bot guide (llmcord context)

The help bot answers questions in one channel from a knowledge file. It uses llmcord with a small wrapper, `run.py`.

## Layout

Create this tree in the new project.

```
project/
  .env                  from templates/env.example
  knowledge.md          the facts the bot answers from
  build-bot-config.sh   writes llmcord/config.yaml
  docker-compose.yaml
  llmcord/              git clone of llmcord, plus Dockerfile and requirements.txt from templates/helpbot
  bot/                  run.py, plus keyclaim.py, teams.py, teamflow.py when used
  secrets/keys.csv      only for the key claim feature
  data/                 claims.json and teams.json
```

`sync-guide-channel.py` expects to live in a `scripts/` directory one level below the project root.

## Bot setup in the Developer Portal

1. Create an application. Open Bot, then Reset Token. Store it as `DISCORD_BOT_TOKEN`.
2. Turn on Message Content Intent and Server Members Intent.
3. Copy the Application ID into `DISCORD_CLIENT_ID`.
4. Invite the bot with this URL. The `permissions=8` value is Administrator.
   `https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot%20applications.commands&permissions=8`
5. Server Settings > Roles: drag the bot role above every role the bot creates or assigns.

Administrator lets the bot build the server without a hand-made permission list. Use a separate bot with narrow permissions for a server that you do not own.

## Run order

1. Fill `.env` with the token, guild id and help bot values.
2. Run `templates/server/bootstrap.sh --check-spec spec.json`.
3. Run `templates/server/bootstrap.sh spec.json .env`. This creates the server and writes the ids into `.env`.
4. Write `knowledge.md`.
5. Run `./build-bot-config.sh`.
6. Run `docker compose up -d --build`.
7. Run `docker compose up -d --force-recreate` after any `.env` change.

## What the wrapper adds to llmcord

| Feature | Behavior |
|---|---|
| Question trigger | The bot answers question-like messages without a mention |
| Organizer skip | The bot ignores unprompted organizer messages. A mention overrides |
| Secret deletion | The bot deletes a message that holds a key or token and warns the author |
| `[[OFFTOPIC]]` | The bot stays silent or points to the right channel |
| `[[UNKNOWN]]` | The bot posts a canned line and pings the organizer role |
| `/getkey`, `/reset-key` | One key per member from `secrets/keys.csv`, matched by email. Needs `GETKEY` |
| `/add-organizer` | An organizer adds another organizer |
| Typed-text cleanup | The bot deletes typed text from non-organizers in the key channel |
| Member role grant | The bot grants the member role after `/getkey` |
| Team button and `/team` | Teams of 1 to 4 with private voice rooms. Needs `TEAM_FINDER` |

## Write a good knowledge file

- State each fact once, with the exact command or value.
- Put one `##` heading per topic. Run `sync-guide-channel.py` to publish those as embeds and write `guide-index.md`.
- Keep deadlines as Discord timestamps. Use `substitutions.json` so the source stays plain text.
- Leave out secrets. The prompt carries the whole file.

## Test

- Run `templates/helpbot/e2e-test.sh` with the dummy bot. It posts questions and reads the replies back.
- Skip cases with `SKIP_CASES="4 6"`.
- Test slash commands and buttons by hand with a normal account. A bot cannot run them.
