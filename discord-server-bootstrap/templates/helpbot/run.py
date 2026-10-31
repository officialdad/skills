import asyncio
import hashlib
import importlib.util
import logging
import os
import re
import sys
import types

import discord
from discord import app_commands

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

log = logging.getLogger("help-bot")

KEYS_PATH = os.environ.get("KEYS_PATH", "/secrets/keys.csv")
CLAIMS_PATH = os.environ.get("CLAIMS_PATH", "/data/claims.json")
ORGANIZER_ROLE_ID = int(os.environ["DISCORD_ORGANIZER_ROLE_ID"])
HELP_CHANNEL_ID = int(os.environ["DISCORD_HELP_CHANNEL_ID"])
COMMUNITY_NAME = os.environ.get("COMMUNITY_NAME", "this server")
COMMUNITY_TOPIC = os.environ.get("COMMUNITY_TOPIC", "this community")


def optional_id(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    return int(value) if value else None


# Each optional feature switches on when its channel or role id exists in the env, and stays off otherwise.
GETKEY_CHANNEL_ID = optional_id("DISCORD_GETKEY_CHANNEL_ID")
TEAM_FINDER_CHANNEL_ID = optional_id("DISCORD_TEAM_FINDER_CHANNEL_ID")
MEMBER_ROLE_ID = optional_id("DISCORD_MEMBER_ROLE_ID")
TEAMS_PATH = os.environ.get("TEAMS_PATH", "/data/teams.json")
TEST_BOT_IDS = {int(i) for i in os.environ.get("TEST_BOT_IDS", "").split(",") if i.strip()}

QUESTION_OPENER = re.compile(
    r"^(how|what|why|where|when|which|who|can|could|does|do|did|is|are|will|should|any ?one|help)\b", re.IGNORECASE
)
ERROR_HINT = re.compile(
    r"\b(error|errors|failed|fails|failing|stuck|not working|doesn'?t work|won'?t|can'?t|cannot|40[0-9]|422)\b", re.IGNORECASE
)
MIN_QUESTION_LENGTH = 10

SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}|\bBearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE)
SECRET_WARNING = "{mention} I deleted your message because it contained a key or token."
SECRET_WARNING_UNDELETED = (
    "{mention} Your message contains a key or token and I can't delete it. Delete it yourself now. "
    "Never post keys, tokens or passwords in Discord."
)

OFFTOPIC_TOKEN = "[[OFFTOPIC]]"
UNKNOWN_TOKEN = "[[UNKNOWN]]"
UNKNOWN_REPLY = f"An organizer may have more information on this: <@&{ORGANIZER_ROLE_ID}>"
OFFTOPIC_REPLIES = (
    f"That one is outside my area. Ask me about {COMMUNITY_TOPIC} and I'm on it.",
    f"Great question for a different bot. I only know {COMMUNITY_TOPIC}.",
    f"I'd love to help, but my whole job is {COMMUNITY_TOPIC}. Try me on that.",
    f"Not my department. I'm here for {COMMUNITY_TOPIC}.",
    f"My expertise starts and ends at {COMMUNITY_TOPIC}. Ask me about that.",
)


def sounds_like_question(text: str) -> bool:
    text = text.strip()
    if len(text) < MIN_QUESTION_LENGTH:
        return False
    return "?" in text or bool(QUESTION_OPENER.match(text)) or bool(ERROR_HINT.search(text))


def is_human_author(message: discord.Message, bot_user: discord.ClientUser) -> bool:
    return message.author.id != bot_user.id and (not message.author.bot or message.author.id in TEST_BOT_IDS)


async def delete_and_warn(message: discord.Message) -> None:
    mention = message.author.mention
    try:
        await message.delete()
        warning = SECRET_WARNING
    except discord.NotFound:
        return
    except discord.Forbidden:
        logging.warning("Missing Manage Messages in channel %s, can't delete a message with a secret", message.channel.id)
        warning = SECRET_WARNING_UNDELETED
    await message.channel.send(warning.format(mention=mention), allowed_mentions=discord.AllowedMentions(users=[message.author]))


def is_organizer_member(author: discord.abc.User) -> bool:
    return any(role.id == ORGANIZER_ROLE_ID for role in getattr(author, "roles", ()))


async def remove_typed_message(message: discord.Message) -> None:
    try:
        await message.delete()
    except discord.NotFound:
        return
    except discord.Forbidden:
        logging.warning("Missing Manage Messages in channel %s, can't delete typed text", message.channel.id)
        return
    await message.channel.send(
        f"{message.author.mention} Type `/getkey` and pick the command. Typed messages are deleted here.",
        delete_after=10,
        allowed_mentions=discord.AllowedMentions(users=[message.author]),
    )


def canned_reply(model_text: str, request_messages: list) -> str | None:
    if UNKNOWN_TOKEN in model_text:
        return UNKNOWN_REPLY
    if OFFTOPIC_TOKEN in model_text:
        # Hashing the question keeps the reply the same for the same message, with variety across messages.
        digest = hashlib.sha256(str(request_messages[-1]["content"]).encode()).digest()
        return OFFTOPIC_REPLIES[digest[0] % len(OFFTOPIC_REPLIES)]
    return None


async def swap_sentinels(stream, request_messages: list):
    # llmcord sends plain replies only after the stream ends, so buffering here adds no visible delay.
    chunks = []
    model_text = ""
    async for chunk in stream:
        chunks.append(chunk)
        if chunk.choices:
            model_text += chunk.choices[0].delta.content or ""

    canned = canned_reply(model_text, request_messages)
    if canned is None:
        for chunk in chunks:
            yield chunk
        return

    delta = types.SimpleNamespace(content=canned)
    yield types.SimpleNamespace(choices=[types.SimpleNamespace(finish_reason="stop", delta=delta)])


def install_canned_replies() -> None:
    from openai.resources.chat.completions import AsyncCompletions

    original_create = AsyncCompletions.create

    async def create(self, *args, **kwargs):
        stream = await original_create(self, *args, **kwargs)
        if not kwargs.get("stream"):
            return stream
        return swap_sentinels(stream, kwargs["messages"])

    AsyncCompletions.create = create


def is_directed_at_a_person(message: discord.Message, bot_user: discord.ClientUser) -> bool:
    # A reply to, or mention of, another human means two people are talking. Interrupting would be noise.
    if any(user.id != bot_user.id for user in message.mentions):
        return True
    reference = message.reference.resolved if message.reference else None
    return isinstance(reference, discord.Message) and reference.author.id != bot_user.id


def make_question_triggers_bot(bot):
    original_on_message = bot.on_message

    async def on_message(message: discord.Message) -> None:
        # Typing is open in the key channel only so /getkey can be used. Typed text can hold an email or key, so it goes at once.
        if message.channel.id == GETKEY_CHANNEL_ID and is_human_author(message, bot.user) and not is_organizer_member(message.author):
            await remove_typed_message(message)
            return

        # Delete before llmcord runs, so the secret never reaches the model.
        if message.guild is not None and is_human_author(message, bot.user) and SECRET_PATTERN.search(message.content):
            await delete_and_warn(message)
            return

        # llmcord drops every bot author. A listed test bot must pass as a human to exercise the real path.
        if message.author.id in TEST_BOT_IDS:
            message.author._user.bot = False

        in_help = message.channel.id == HELP_CHANNEL_ID or getattr(message.channel, "parent_id", None) == HELP_CHANNEL_ID
        is_organizer = any(role.id == ORGANIZER_ROLE_ID for role in getattr(message.author, "roles", ()))
        replies_to_bot = (
            message.reference is not None
            and isinstance(message.reference.resolved, discord.Message)
            and message.reference.resolved.author.id == bot.user.id
        )

        if in_help and not message.author.bot and bot.user not in message.mentions:
            if replies_to_bot:
                message.mentions.append(bot.user)
            elif not is_organizer and not is_directed_at_a_person(message, bot.user) and sounds_like_question(message.content):
                message.mentions.append(bot.user)

        await original_on_message(message)

    async def on_message_edit(_before: discord.Message, after: discord.Message) -> None:
        if after.guild is not None and is_human_author(after, bot.user) and SECRET_PATTERN.search(after.content):
            await delete_and_warn(after)

    bot.on_message = on_message
    bot.add_listener(on_message_edit, "on_message_edit")


async def grant_member_role(interaction: discord.Interaction) -> None:
    # Runs after the key reply, so a role error never blocks a member from getting their key.
    role = interaction.guild.get_role(MEMBER_ROLE_ID) if MEMBER_ROLE_ID else None
    member = interaction.user
    if role is None or role in member.roles:
        return
    try:
        await member.add_roles(role, reason="Claimed a key with /getkey")
    except discord.HTTPException as error:
        log.error("can't grant the member role to user=%s: %s", member.id, error)


def register_commands(bot):
    @bot.tree.command(name="add-organizer", description="Give a member the Organizer role")
    @app_commands.guild_only()
    @app_commands.describe(member="The member to make an organizer")
    async def add_organizer(interaction: discord.Interaction, member: discord.Member) -> None:
        if not any(role.id == ORGANIZER_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Only organizers can use this command.", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("A bot can't be an organizer.", ephemeral=True)
            return

        organizer_role = interaction.guild.get_role(ORGANIZER_ROLE_ID)
        if organizer_role is None:
            await interaction.response.send_message("The Organizer role no longer exists. Run bootstrap.sh again.", ephemeral=True)
            return

        if organizer_role in member.roles:
            await interaction.response.send_message(f"{member.mention} is already an organizer.", ephemeral=True)
            return

        try:
            await member.add_roles(organizer_role, reason=f"Added by {interaction.user} via /add-organizer")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I can't assign that role. Move my role above Organizer in Server Settings > Roles, and give me Manage Roles.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"{member.mention} is now an organizer, added by {interaction.user.mention}.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    if TEAM_FINDER_CHANNEL_ID:
        from teamflow import register_team_features
        from teams import TeamStore

        register_team_features(bot, TeamStore(TEAMS_PATH), TEAM_FINDER_CHANNEL_ID, ORGANIZER_ROLE_ID)

    if GETKEY_CHANNEL_ID:
        register_key_commands(bot)


def register_key_commands(bot):
    from keyclaim import ClaimStore, FailureLimiter, claim_key, load_keys, mask_email, normalize_email

    claim_store = ClaimStore(CLAIMS_PATH)
    limiter = FailureLimiter()

    # Every reply is ephemeral because a key posted in the channel would leak to all members.
    @bot.tree.command(name="getkey", description="Get your personal AI key. Only you can see the reply.")
    @app_commands.guild_only()
    @app_commands.describe(email="The email address you registered with")
    async def getkey(interaction: discord.Interaction, email: str) -> None:
        user_id = interaction.user.id
        if interaction.channel_id != GETKEY_CHANNEL_ID:
            await interaction.response.send_message(f"Run /getkey in <#{GETKEY_CHANNEL_ID}>.", ephemeral=True)
            return

        if limiter.blocked(user_id):
            await interaction.response.send_message("Too many wrong emails. Try again in an hour or ask an organizer.", ephemeral=True)
            return

        try:
            keys = load_keys(KEYS_PATH)
        except FileNotFoundError:
            log.error("key list not found at %s", KEYS_PATH)
            await interaction.response.send_message("Keys aren't loaded yet. Ask an organizer.", ephemeral=True)
            return

        result = claim_key(keys, claim_store, email, user_id)
        masked = mask_email(normalize_email(email))
        log.info("getkey user=%s email=%s status=%s", user_id, masked, result.status)

        if result.status in ("claimed", "repeat"):
            await interaction.response.send_message(
                f"Your key:\n```\n{result.key}\n```\nKeep it private. Set it up with the setup command in the guide, step 2.",
                ephemeral=True,
            )
            await grant_member_role(interaction)
            return

        if result.status == "not_found":
            limiter.record(user_id)
            message = "No key for that email. Check the spelling, or ask an organizer if you registered with a different address."
        elif result.status == "taken":
            limiter.record(user_id)
            message = "That key was already claimed by another Discord account. Tell an organizer if it wasn't you."
        else:
            message = "You already have a key under another email. Ask an organizer if that's wrong."
        await interaction.response.send_message(message, ephemeral=True)

    @bot.tree.command(name="reset-key", description="Let an email claim its key again")
    @app_commands.guild_only()
    @app_commands.describe(email="The email whose claim to release")
    async def reset_key(interaction: discord.Interaction, email: str) -> None:
        if not any(role.id == ORGANIZER_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Only organizers can use this command.", ephemeral=True)
            return

        released = claim_store.clear(normalize_email(email))
        log.info("reset-key by=%s email=%s released=%s", interaction.user.id, mask_email(normalize_email(email)), released)
        await interaction.response.send_message("Claim released." if released else "That email has no claim.", ephemeral=True)


def main() -> None:
    spec = importlib.util.spec_from_file_location("llmcord", "/app/llmcord.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["llmcord"] = module

    install_canned_replies()
    real_run = asyncio.run

    def run_with_commands(coro, **kwargs):
        register_commands(module.discord_bot)
        make_question_triggers_bot(module.discord_bot)
        return real_run(coro, **kwargs)

    asyncio.run = run_with_commands
    spec.loader.exec_module(module)


main()
