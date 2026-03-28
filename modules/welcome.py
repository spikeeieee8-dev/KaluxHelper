"""
WELCOME MODULE
Sends a rich welcome embed when members join the server.

Features:
  - Configurable welcome channel, message, and optional role auto-assign
  - Enable/disable toggle
  - !testwelcome command to preview the welcome message
  - Fully persistent settings via SQLite
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import datetime

from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, error, warn


# ─── DB Init ──────────────────────────────────────────────────────────────────

async def _init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS welcome_settings (
                guild_id    TEXT PRIMARY KEY,
                channel_id  TEXT,
                message     TEXT NOT NULL DEFAULT 'Welcome to the server, {user}! We''re glad to have you.',
                role_id     TEXT,
                enabled     INTEGER NOT NULL DEFAULT 1
            );
        """)
        await db.commit()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_settings(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM welcome_settings WHERE guild_id = ?", (str(guild_id),)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


async def _upsert(guild_id: int, **kwargs) -> None:
    settings = await _get_settings(guild_id)
    defaults = {
        "channel_id": settings.get("channel_id"),
        "message": settings.get("message", "Welcome to the server, {user}! We're glad to have you."),
        "role_id": settings.get("role_id"),
        "enabled": settings.get("enabled", 1),
    }
    defaults.update(kwargs)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO welcome_settings (guild_id, channel_id, message, role_id, enabled)
            VALUES (:guild_id, :channel_id, :message, :role_id, :enabled)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                message    = excluded.message,
                role_id    = excluded.role_id,
                enabled    = excluded.enabled
        """, {"guild_id": str(guild_id), **defaults})
        await db.commit()


def _format_message(template: str, member: discord.Member) -> str:
    return (
        template
        .replace("{user}", member.mention)
        .replace("{username}", member.display_name)
        .replace("{server}", member.guild.name)
        .replace("{count}", str(member.guild.member_count))
    )


async def _send_welcome(member: discord.Member, settings: dict) -> None:
    if not settings.get("enabled", 1):
        return
    if not settings.get("channel_id"):
        return

    channel = member.guild.get_channel(int(settings["channel_id"]))
    if not channel:
        return

    msg = _format_message(
        settings.get("message", "Welcome to the server, {user}! We're glad to have you."),
        member
    )

    embed = discord.Embed(
        description=msg,
        color=COLOR_BRAND,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    embed.set_author(
        name=f"Welcome to {member.guild.name}!",
        icon_url=member.guild.icon.url if member.guild.icon else None,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="Member #", value=f"#{member.guild.member_count}", inline=True)
    embed.set_footer(text=f"ID: {member.id}")

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass

    # Auto-assign welcome role if configured
    role_id = settings.get("role_id")
    if role_id:
        role = member.guild.get_role(int(role_id))
        if role:
            try:
                await member.add_roles(role, reason="Welcome auto-role")
            except discord.Forbidden:
                pass


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Welcome(commands.Cog, name="Welcome"):
    """👋 Welcome messages when members join the server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = await _get_settings(member.guild.id)
        await _send_welcome(member, settings)

    # ── Commands ──────────────────────────────────────────────────────────────

    @commands.command(name="setwelcome", aliases=["welcomechannel"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setwelcome_cmd(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the channel where welcome messages are sent."""
        ch = channel or ctx.channel
        await _upsert(ctx.guild.id, channel_id=str(ch.id))
        await ctx.reply(embed=success(f"Welcome channel set to {ch.mention}"), mention_author=False)

    @commands.command(name="setwelcomemessage", aliases=["welcomemsg"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setwelcomemessage_cmd(self, ctx: commands.Context, *, message: str):
        """Set the welcome message. Use {user}, {username}, {server}, {count} as placeholders."""
        if len(message) > 500:
            return await ctx.reply(embed=error("Message must be 500 characters or less."), mention_author=False)
        await _upsert(ctx.guild.id, message=message)
        await ctx.reply(
            embed=success(f"Welcome message updated.\nPreview: {_format_message(message, ctx.author)}"),
            mention_author=False,
        )

    @commands.command(name="setwelcomerole", aliases=["welcomerole"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setwelcomerole_cmd(self, ctx: commands.Context, role: discord.Role = None):
        """Set a role to auto-assign on join. Use without a role to clear."""
        await _upsert(ctx.guild.id, role_id=str(role.id) if role else None)
        if role:
            await ctx.reply(embed=success(f"Welcome role set to {role.mention}. New members will receive it automatically."), mention_author=False)
        else:
            await ctx.reply(embed=success("Welcome role cleared. No role will be auto-assigned."), mention_author=False)

    @commands.command(name="welcomeon")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def welcomeon_cmd(self, ctx: commands.Context):
        """Enable welcome messages."""
        await _upsert(ctx.guild.id, enabled=1)
        await ctx.reply(embed=success("Welcome messages **enabled**."), mention_author=False)

    @commands.command(name="welcomeoff")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def welcomeoff_cmd(self, ctx: commands.Context):
        """Disable welcome messages."""
        await _upsert(ctx.guild.id, enabled=0)
        await ctx.reply(embed=success("Welcome messages **disabled**."), mention_author=False)

    @commands.command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def testwelcome_cmd(self, ctx: commands.Context):
        """Preview the welcome message as if you just joined."""
        settings = await _get_settings(ctx.guild.id)
        if not settings:
            return await ctx.reply(embed=warn("No welcome settings configured. Use `!setwelcome #channel` first."), mention_author=False)
        if not settings.get("enabled", 1):
            return await ctx.reply(embed=warn("Welcome messages are currently **disabled**. Enable with `!welcomeon`."), mention_author=False)
        if not settings.get("channel_id"):
            return await ctx.reply(embed=warn("No welcome channel set. Use `!setwelcome #channel` first."), mention_author=False)

        await _send_welcome(ctx.author, settings)
        await ctx.reply(embed=success("Test welcome message sent!"), mention_author=False)

    @commands.command(name="welcomeconfig")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def welcomeconfig_cmd(self, ctx: commands.Context):
        """View current welcome configuration."""
        settings = await _get_settings(ctx.guild.id)

        channel_id = settings.get("channel_id")
        channel = ctx.guild.get_channel(int(channel_id)) if channel_id else None
        role_id = settings.get("role_id")
        role = ctx.guild.get_role(int(role_id)) if role_id else None

        embed = discord.Embed(
            title="👋 Welcome Configuration",
            color=COLOR_BRAND,
        )
        embed.add_field(name="Status",   value="🟢 Enabled" if settings.get("enabled", 1) else "🔴 Disabled", inline=True)
        embed.add_field(name="Channel",  value=channel.mention if channel else "Not set",                     inline=True)
        embed.add_field(name="Auto-Role",value=role.mention if role else "None",                              inline=True)
        embed.add_field(
            name="Message Template",
            value=f"```{settings.get('message', 'Not set')}```",
            inline=False,
        )
        embed.set_footer(text="Use !setwelcome, !setwelcomemessage, !setwelcomerole to configure")
        await ctx.reply(embed=embed, mention_author=False)

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="testwelcome", description="Preview the welcome message")
    @app_commands.default_permissions(administrator=True)
    async def slash_testwelcome(self, interaction: discord.Interaction):
        settings = await _get_settings(interaction.guild.id)
        if not settings or not settings.get("channel_id"):
            return await interaction.response.send_message(
                embed=warn("No welcome channel configured. Use `!setwelcome #channel` first."), ephemeral=True
            )
        await _send_welcome(interaction.user, settings)
        await interaction.response.send_message(embed=success("Test welcome message sent!"), ephemeral=True)


# ─── Setup ────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await _init_db()
    await bot.add_cog(Welcome(bot))
