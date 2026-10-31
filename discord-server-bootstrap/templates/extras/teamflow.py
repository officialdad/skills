import logging

import discord
from discord import app_commands

from teams import MAX_NAME_LENGTH, MAX_TEAM_SIZE, TeamStore

log = logging.getLogger("help-bot")

BUTTON_ID = "community-team-form"
PIN_TITLE = f"**Teams are 1 to {MAX_TEAM_SIZE} people.**"
CHANNEL_PREFIX = "👥｜"
ROOM_ACCESS = dict(view_channel=True, connect=True, speak=True, stream=True, use_voice_activation=True)

REJECTIONS = {
    "bad_name": f"Pick a team name of 1 to {MAX_NAME_LENGTH} characters.",
    "too_many": f"A team has at most {MAX_TEAM_SIZE} people.",
    "name_taken": "A team with that name exists. Pick another name.",
}


def is_organizer(member: discord.abc.User, organizer_role_id: int) -> bool:
    return any(role.id == organizer_role_id for role in getattr(member, "roles", ()))


def register_team_features(bot, store: TeamStore, team_finder_id: int, organizer_role_id: int) -> None:
    async def delete_room(guild: discord.Guild, channel_id: int, reason: str) -> None:
        channel = guild.get_channel(channel_id)
        if channel is None:
            return
        try:
            await channel.delete(reason=reason)
        except discord.NotFound:
            pass

    async def create_room(guild: discord.Guild, team_name: str, members: list[discord.Member]) -> discord.VoiceChannel:
        finder = guild.get_channel(team_finder_id)
        organizer_role = guild.get_role(organizer_role_id)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        for member in members:
            overwrites[member] = discord.PermissionOverwrite(**ROOM_ACCESS)
        if organizer_role:
            overwrites[organizer_role] = discord.PermissionOverwrite(**ROOM_ACCESS)
        return await guild.create_voice_channel(
            f"{CHANNEL_PREFIX}{team_name}"[:100],
            category=finder.category if finder else None,
            overwrites=overwrites,
            reason=f"Team {team_name} formed",
        )

    async def form_team(interaction: discord.Interaction, name: str, picked: list[discord.abc.User]) -> None:
        creator = interaction.user
        teammates = [user for user in picked if user.id != creator.id]
        if any(user.bot for user in teammates):
            await interaction.followup.send("A bot can't join a team.", ephemeral=True)
            return

        members = [creator, *teammates]
        result = store.create(name, [member.id for member in members])
        if result.status == "already_on_team":
            who = "You are" if result.user_id == creator.id else f"<@{result.user_id}> is"
            await interaction.followup.send(
                f"{who} already on a team. Leave it first with /team leave.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        if result.status != "ok":
            await interaction.followup.send(REJECTIONS[result.status], ephemeral=True)
            return

        team = result.team
        try:
            room = await create_room(interaction.guild, team.name, members)
        except discord.HTTPException as error:
            # The name and members are already reserved in the store, so release them or the team could never retry.
            store.remove(team.name)
            log.error("can't create the voice channel for team %s: %s", team.name, error)
            await interaction.followup.send("I couldn't create the voice channel. Try again or ask an organizer.", ephemeral=True)
            return

        store.set_channel(team.name, room.id)
        log.info("team formed name=%s size=%s by=%s", team.name, len(members), creator.id)
        await interaction.followup.send(f"Your team room is ready: {room.mention}", ephemeral=True)
        await interaction.channel.send(
            f"**Team {team.name}** formed: {' '.join(member.mention for member in members)}\nVoice room: {room.mention}",
            allowed_mentions=discord.AllowedMentions(users=members),
        )

    class TeamModal(discord.ui.Modal, title="Form a team"):
        def __init__(self) -> None:
            super().__init__()
            self.name_input = discord.ui.TextInput(placeholder="For example: Pumpkin Patch", max_length=MAX_NAME_LENGTH)
            self.members_input = discord.ui.UserSelect(
                placeholder="Pick your teammates", min_values=0, max_values=MAX_TEAM_SIZE - 1, required=False
            )
            self.add_item(discord.ui.Label(text="Team name", component=self.name_input))
            self.add_item(discord.ui.Label(text=f"Teammates (up to {MAX_TEAM_SIZE - 1}, you are added for you)", component=self.members_input))

        async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await form_team(interaction, self.name_input.value, list(self.members_input.values))

    class FormTeamView(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)

        @discord.ui.button(label="Form a team", emoji="👥", style=discord.ButtonStyle.success, custom_id=BUTTON_ID)
        async def form(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
            current = store.team_of(interaction.user.id)
            if current:
                await interaction.response.send_message(
                    f"You are already on team **{current.name}**. Leave it first with /team leave.", ephemeral=True
                )
                return
            await interaction.response.send_modal(TeamModal())

    async def ensure_button_message() -> None:
        channel = bot.get_channel(team_finder_id)
        if channel is None:
            log.error("team-finder channel %s not found, no button posted", team_finder_id)
            return
        text = (
            f"{PIN_TITLE}\n"
            "Click the button to name your team and pick your teammates. "
            "The bot creates a private voice room for the team.\n"
            "Looking for teammates? Post your skills and the game you want to make below.\n"
            "Someone joins your team later? Run `/team add`. Left the wrong team? Run `/team leave`."
        )
        async for pinned in channel.pins():
            message = pinned.message if hasattr(pinned, "message") else pinned
            if message.content.startswith(PIN_TITLE) and message.author.id == bot.user.id:
                if message.content != text:
                    await message.edit(content=text)
                return
        message = await channel.send(text, view=FormTeamView())
        await message.pin()

    view_registered = False

    async def on_ready() -> None:
        # on_ready fires again after a reconnect, and the persistent view must be added only once.
        nonlocal view_registered
        if not view_registered:
            bot.add_view(FormTeamView())
            view_registered = True
        await ensure_button_message()

    bot.add_listener(on_ready, "on_ready")

    team = app_commands.Group(name="team", description="Teams", guild_only=True)

    @team.command(name="leave", description="Leave your team")
    async def leave(interaction: discord.Interaction) -> None:
        outcome = store.leave(interaction.user.id)
        if outcome is None:
            await interaction.response.send_message("You are not on a team.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        room = interaction.guild.get_channel(outcome.team.channel_id)
        if outcome.disbanded:
            await delete_room(interaction.guild, outcome.team.channel_id, f"Team {outcome.team.name} is empty")
            await interaction.followup.send(f"You left **{outcome.team.name}**. It had no one left, so it is gone.", ephemeral=True)
            return
        if room:
            await room.set_permissions(interaction.user, overwrite=None, reason="Left the team")
        await interaction.followup.send(f"You left **{outcome.team.name}**.", ephemeral=True)

    @team.command(name="add", description="Add a member to your team")
    @app_commands.describe(member="The person to add", team_name="Organizers only: the team to add them to")
    @app_commands.rename(team_name="team")
    async def add(interaction: discord.Interaction, member: discord.Member, team_name: str | None = None) -> None:
        organizer = is_organizer(interaction.user, organizer_role_id)
        if team_name and not organizer:
            await interaction.response.send_message("Only organizers can add people to another team.", ephemeral=True)
            return
        target = store.get(team_name) if team_name else store.team_of(interaction.user.id)
        if target is None:
            reply = "No team with that name." if team_name else f"You are not on a team. Form one with the button in <#{team_finder_id}>."
            await interaction.response.send_message(reply, ephemeral=True)
            return
        if member.bot:
            await interaction.response.send_message("A bot can't join a team.", ephemeral=True)
            return

        result = store.add_member(target.name, member.id)
        if result.status != "ok":
            rejections = {
                "full": f"**{target.name}** already has {MAX_TEAM_SIZE} people.",
                "already_member": f"{member.mention} is already on **{target.name}**.",
                "already_on_team": f"{member.mention} is already on another team. They must run /team leave first.",
            }
            await interaction.response.send_message(rejections[result.status], ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return

        await interaction.response.defer(ephemeral=True)
        room = interaction.guild.get_channel(target.channel_id)
        try:
            if room is None:
                raise discord.NotFound(None, "team room is gone")
            await room.set_permissions(member, overwrite=discord.PermissionOverwrite(**ROOM_ACCESS), reason=f"Added to {target.name}")
        except discord.HTTPException as error:
            # The member was saved before the room was opened, so undo it or they would count toward the team without access.
            store.leave(member.id)
            log.error("can't open team room for user=%s team=%s: %s", member.id, target.name, error)
            await interaction.followup.send("I couldn't give them access to the team room. Ask an organizer.", ephemeral=True)
            return

        log.info("team add name=%s user=%s by=%s", target.name, member.id, interaction.user.id)
        await interaction.followup.send(f"Added {member.mention} to **{target.name}**.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        finder = interaction.guild.get_channel(team_finder_id)
        if finder:
            await finder.send(
                f"{member.mention} joined **Team {target.name}**. Voice room: {room.mention}",
                allowed_mentions=discord.AllowedMentions(users=[member]),
            )

    @add.autocomplete("team_name")
    async def add_team_names(_interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=each.name, value=each.name) for each in store.all() if current.casefold() in each.name.casefold()][:25]

    @team.command(name="disband", description="Remove a team and its voice room")
    @app_commands.describe(name="The team name")
    async def disband(interaction: discord.Interaction, name: str) -> None:
        if not is_organizer(interaction.user, organizer_role_id):
            await interaction.response.send_message("Only organizers can use this command.", ephemeral=True)
            return
        removed = store.remove(name)
        if removed is None:
            await interaction.response.send_message("No team with that name.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await delete_room(interaction.guild, removed.channel_id, f"Team {removed.name} disbanded by {interaction.user}")
        await interaction.followup.send(f"Removed team **{removed.name}**.", ephemeral=True)

    @team.command(name="cleanup", description="Remove every team and voice room. Run after the pitches.")
    @app_commands.describe(confirm="Set to true to confirm")
    async def cleanup(interaction: discord.Interaction, confirm: bool) -> None:
        if not is_organizer(interaction.user, organizer_role_id):
            await interaction.response.send_message("Only organizers can use this command.", ephemeral=True)
            return
        if not confirm:
            await interaction.response.send_message("Nothing removed. Set confirm to true to remove all teams.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        teams = store.all()
        for each in teams:
            store.remove(each.name)
            await delete_room(interaction.guild, each.channel_id, f"Cleanup by {interaction.user}")
        log.info("team cleanup by=%s removed=%s", interaction.user.id, len(teams))
        await interaction.followup.send(f"Removed {len(teams)} teams and their voice rooms.", ephemeral=True)

    @disband.autocomplete("name")
    async def team_names(_interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=each.name, value=each.name) for each in store.all() if current.casefold() in each.name.casefold()][:25]

    bot.tree.add_command(team)
