"""Avengers Mate - tournament helper bot.

Commands:
  /tourney rules  - post rules in a channel and remember it as the ping channel
  /trole          - choose the role /tmembers will assign
  /tmembers       - give one member the active tourney role
  /alert          - DM up to 10 members + post a real @role ping publicly
  /timer          - IST date/time alarm that pings a member or role
"""

import asyncio
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask

import config

GUILD = discord.Object(id=config.GUILD_ID)
IST = ZoneInfo("Asia/Kolkata")

intents = discord.Intents.default()  # no privileged intents needed
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

PING = discord.AllowedMentions(users=True, roles=True, everyone=False)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
async def send_private(interaction: discord.Interaction, message: str) -> None:
    """Reply only to the admin, whether or not we already deferred."""
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def is_admin(interaction: discord.Interaction) -> bool:
    """Official server + admin role only."""
    if interaction.guild is None or interaction.guild.id != config.GUILD_ID:
        raise app_commands.CheckFailure("wrong_server")
    member = interaction.user
    if not isinstance(member, discord.Member):
        raise app_commands.CheckFailure("no_role")
    if config.ADMIN_ROLE_ID not in {role.id for role in member.roles}:
        raise app_commands.CheckFailure("no_role")
    return True


def announcement_channel(interaction: discord.Interaction) -> discord.TextChannel | None:
    """Channel remembered from /tourney rules, falling back to current channel."""
    channel_id = config.state["announcement_channel_id"]
    channel = interaction.guild.get_channel(channel_id) if channel_id else None
    if channel is None and isinstance(interaction.channel, discord.TextChannel):
        channel = interaction.channel
    return channel


@tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CheckFailure):
        reason = str(error)
        if reason == "wrong_server":
            text = "This bot only works in the official server."
        elif reason == "no_role":
            text = f"You need the admin role (<@&{config.ADMIN_ROLE_ID}>) to use this."
        else:
            text = "You are not allowed to use this command."
        await send_private(interaction, text)
        return

    print(f"Command error: {error}")
    await send_private(interaction, "Something went wrong. Check the bot logs on Render.")


# --------------------------------------------------------------------------- #
# /tourney rules
# --------------------------------------------------------------------------- #
class TourneyGroup(app_commands.Group):
    def __init__(self) -> None:
        super().__init__(name="tourney", description="Tournament tools")

    @app_commands.command(name="rules", description="Post tournament rules in a channel")
    @app_commands.describe(
        channel="Channel where the rules will be posted",
        rule1="Rule 1 (required)",
        rule2="Rule 2",
        rule3="Rule 3",
        rule4="Rule 4",
        rule5="Rule 5",
    )
    @app_commands.check(is_admin)
    async def rules(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        rule1: str,
        rule2: str = None,
        rule3: str = None,
        rule4: str = None,
        rule5: str = None,
    ) -> None:
        rules = [rule for rule in (rule1, rule2, rule3, rule4, rule5) if rule and rule.strip()]
        description = "\n".join(f"**{i}.** {rule.strip()}" for i, rule in enumerate(rules, 1))

        embed = discord.Embed(
            title="🏆 Tournament Rules",
            description=description,
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Posted by {interaction.user.display_name}")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await send_private(interaction, f"I can't send messages in {channel.mention}.")
            return

        config.state["announcement_channel_id"] = channel.id
        await send_private(
            interaction,
            f"Rules posted in {channel.mention}. I'll use that channel for tournament pings.",
        )


# --------------------------------------------------------------------------- #
# /trole
# --------------------------------------------------------------------------- #
@tree.command(name="trole", description="Set the role that /tmembers will assign", guild=GUILD)
@app_commands.describe(role="The tournament participants role")
@app_commands.check(is_admin)
async def trole(interaction: discord.Interaction, role: discord.Role) -> None:
    config.state["tourney_role_id"] = role.id
    await send_private(interaction, f"Done. /tmembers will now give {role.mention}.")


# --------------------------------------------------------------------------- #
# /tmembers
# --------------------------------------------------------------------------- #
@tree.command(name="tmembers", description="Give a member the tournament role", guild=GUILD)
@app_commands.describe(member="The member to add")
@app_commands.check(is_admin)
async def tmembers(interaction: discord.Interaction, member: discord.Member) -> None:
    role = interaction.guild.get_role(config.state["tourney_role_id"])
    if role is None:
        await send_private(interaction, "The tourney role no longer exists. Set it again with /trole.")
        return

    try:
        await member.add_roles(role, reason=f"Added by {interaction.user}")
    except discord.Forbidden:
        await send_private(
            interaction,
            "I can't assign that role. Move my bot role above the tournament role in Server Settings > Roles.",
        )
        return

    channel = announcement_channel(interaction)
    if channel is not None:
        try:
            await channel.send(
                f"✅ {member.mention} joined the tournament. {role.mention}",
                allowed_mentions=PING,
            )
        except discord.Forbidden:
            pass

    await send_private(interaction, f"{member.display_name} got {role.name}.")


# --------------------------------------------------------------------------- #
# /alert
# --------------------------------------------------------------------------- #
@tree.command(name="alert", description="DM up to 10 members and ping the role", guild=GUILD)
@app_commands.describe(
    tourney_name="Tournament name",
    message="Tournament message for the DMs",
    role1="Role to ping publicly",
    role2="Another role to ping publicly (optional)",
    member1="Member 1",
    member2="Member 2",
    member3="Member 3",
    member4="Member 4",
    member5="Member 5",
    member6="Member 6",
    member7="Member 7",
    member8="Member 8",
    member9="Member 9",
    member10="Member 10",
)
@app_commands.check(is_admin)
async def alert(
    interaction: discord.Interaction,
    tourney_name: str,
    message: str,
    role1: discord.Role = None,
    role2: discord.Role = None,
    member1: discord.Member = None,
    member2: discord.Member = None,
    member3: discord.Member = None,
    member4: discord.Member = None,
    member5: discord.Member = None,
    member6: discord.Member = None,
    member7: discord.Member = None,
    member8: discord.Member = None,
    member9: discord.Member = None,
    member10: discord.Member = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    members = [
        member for member in
        (member1, member2, member3, member4, member5,
         member6, member7, member8, member9, member10)
        if member is not None
    ]
    if not members:
        await send_private(interaction, "Pick at least one member in the ping boxes.")
        return

    roles = [role for role in (role1, role2) if role is not None]
    channel = announcement_channel(interaction)
    if channel is None:
        await send_private(interaction, "No channel available. Run /tourney rules first.")
        return

    role_pings = " ".join(role.mention for role in roles)
    public_post = (
        f"📢 **{tourney_name}**\n{message}\n"
        f"{role_pings}\n" + " ".join(member.mention for member in members)
    )

    try:
        announcement = await channel.send(public_post, allowed_mentions=PING)
    except discord.Forbidden:
        await send_private(interaction, f"I can't post in {channel.mention}.")
        return

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="View announcement",
            style=discord.ButtonStyle.link,
            url=announcement.jump_url,
        )
    )

    dm_embed = discord.Embed(
        title=f"🏆 {tourney_name}",
        description=message,
        color=discord.Color.blurple(),
    )
    if roles:
        dm_embed.add_field(
            name="Pinged role(s)",
            value=", ".join(role.name for role in roles),
            inline=False,
        )
    dm_embed.set_footer(text="Open the announcement to see the role ping.")

    sent, failed = 0, 0
    for member in members:
        try:
            await member.send(embed=dm_embed, view=view)
            sent += 1
        except discord.Forbidden:
            failed += 1

    await send_private(
        interaction,
        f"Alert sent: {sent} DM(s) delivered, {failed} failed "
        f"(those members have DMs closed). Public ping: {announcement.jump_url}",
    )


# --------------------------------------------------------------------------- #
# /timer
# --------------------------------------------------------------------------- #
async def run_alarm(delay: float, when: datetime, target: str, channel, setter: str) -> None:
    try:
        await asyncio.sleep(delay)
        embed = discord.Embed(
            title="⏰ Alarm rang!",
            description=f"Scheduled for {when:%d %b %Y, %H:%M} IST",
            color=discord.Color.red(),
        )
        embed.set_footer(text=f"Alarm set by {setter}")
        await channel.send(f"{target} — your timer rang!", embed=embed, allowed_mentions=PING)
    except Exception as exc:  # keep the background task from dying silently
        print(f"Alarm failed: {exc}")


@tree.command(name="timer", description="Set an IST alarm that pings a user or role", guild=GUILD)
@app_commands.describe(
    date="Date in DD/MM/YYYY format (IST)",
    time="Time in HH:MM format (IST)",
    member="Member to ping when it rings",
    role="Role to ping when it rings",
)
@app_commands.check(is_admin)
async def timer(
    interaction: discord.Interaction,
    date: str,
    time: str,
    member: discord.Member = None,
    role: discord.Role = None,
) -> None:
    try:
        naive = datetime.strptime(f"{date.strip()} {time.strip()}", "%d/%m/%Y %H:%M")
    except ValueError:
        await send_private(interaction, "Use DD/MM/YYYY and HH:MM, e.g. 24/11/2026 and 18:30.")
        return

    when = naive.replace(tzinfo=IST)
    delay = (when - datetime.now(IST)).total_seconds()
    if delay <= 0:
        await send_private(interaction, "That time is already in the past. Use a future IST time.")
        return

    if role is not None:
        target = role.mention
    elif member is not None:
        target = member.mention
    else:
        target = interaction.user.mention

    channel = announcement_channel(interaction)
    if channel is None:
        await send_private(interaction, "No channel available. Run /tourney rules first.")
        return

    task = asyncio.create_task(
        run_alarm(delay, when, target, channel, interaction.user.display_name)
    )
    config.state["timers"].append(task)

    await send_private(
        interaction,
        f"Alarm set for **{when:%d %b %Y, %H:%M IST}** ({int(delay // 60)} minutes from now).",
    )


# --------------------------------------------------------------------------- #
# Startup
# --------------------------------------------------------------------------- #
@bot.event
async def setup_hook() -> None:
    tree.add_command(TourneyGroup(), guild=GUILD)
    await tree.sync(guild=GUILD)
    print("Slash commands synced to the official server.")


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


# Tiny web server so Render sees an open port and keeps the bot online.
web = Flask("avengers-mate")


@web.route("/")
def health() -> str:
    return "Avengers Mate is online!"


def keep_awake() -> None:
    web.run(host="0.0.0.0", port=config.PORT)


if __name__ == "__main__":
    threading.Thread(target=keep_awake, daemon=True).start()
    bot.run(config.DISCORD_TOKEN)
