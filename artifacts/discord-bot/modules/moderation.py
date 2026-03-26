"""
MODERATION MODULE
Commands: ban, kick, mute, unmute, warn, warnings, clearwarns, purge, slowmode, lock, unlock
Both prefix and slash variants.
"""
import discord
from discord import app_commands
from discord.ext import commands

from main.utils.database import add_warning, get_warnings, clear_warnings
from main.utils.embeds import success, error, warn, brand


class Moderation(commands.Cog, name="Moderation"):
    """🔨 Moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !ban ─────────────────────────────────────────────────────────────────

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply(embed=error("You can't ban someone with an equal or higher role."), mention_author=False)
        await member.ban(reason=f"{ctx.author} — {reason}")
        await ctx.reply(embed=success(f"Banned **{member}**\nReason: {reason}"), mention_author=False)
        try:
            await member.send(embed=error(f"You were **banned** from **{ctx.guild.name}**.\nReason: {reason}"))
        except discord.Forbidden:
            pass

    # ── !kick ─────────────────────────────────────────────────────────────────

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply(embed=error("You can't kick someone with an equal or higher role."), mention_author=False)
        await member.kick(reason=f"{ctx.author} — {reason}")
        await ctx.reply(embed=success(f"Kicked **{member}**\nReason: {reason}"), mention_author=False)
        try:
            await member.send(embed=warn(f"You were **kicked** from **{ctx.guild.name}**.\nReason: {reason}"))
        except discord.Forbidden:
            pass

    # ── !mute ─────────────────────────────────────────────────────────────────

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute_cmd(self, ctx: commands.Context, member: discord.Member, minutes: int = 10, *, reason: str = "No reason provided"):
        """Timeout (mute) a member for X minutes."""
        import datetime
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"{ctx.author} — {reason}")
        await ctx.reply(embed=success(f"Muted **{member}** for **{minutes}m**\nReason: {reason}"), mention_author=False)

    # ── !unmute ───────────────────────────────────────────────────────────────

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute_cmd(self, ctx: commands.Context, member: discord.Member):
        """Remove a timeout from a member."""
        await member.timeout(None)
        await ctx.reply(embed=success(f"Unmuted **{member}**"), mention_author=False)

    # ── !warn ─────────────────────────────────────────────────────────────────

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def warn_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member."""
        count = await add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        await ctx.reply(embed=warn(f"Warned **{member}**\nReason: {reason}\nTotal warnings: **{count}**"), mention_author=False)
        try:
            await member.send(embed=warn(f"You were **warned** in **{ctx.guild.name}**.\nReason: {reason}"))
        except discord.Forbidden:
            pass

    # ── !warnings ─────────────────────────────────────────────────────────────

    @commands.command(name="warnings", aliases=["warns"])
    @commands.guild_only()
    async def warnings_cmd(self, ctx: commands.Context, member: discord.Member = None):
        """View warnings for a member."""
        m = member or ctx.author
        rows = await get_warnings(ctx.guild.id, m.id)
        embed = brand(f"⚠️ Warnings for {m}")
        if rows:
            lines = [
                f"**{i+1}.** {r['reason']} — <@{r['mod_id']}> <t:{r['created_at']}:R>"
                for i, r in enumerate(rows)
            ]
            embed.description = "\n".join(lines)
        else:
            embed.description = "No warnings on record."
        await ctx.reply(embed=embed, mention_author=False)

    # ── !clearwarns ───────────────────────────────────────────────────────────

    @commands.command(name="clearwarns", aliases=["clearwarnings", "resetwarns"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def clearwarns_cmd(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member."""
        count = await clear_warnings(ctx.guild.id, member.id)
        await ctx.reply(embed=success(f"Cleared **{count}** warning(s) for **{member}**."), mention_author=False)

    # ── !purge ────────────────────────────────────────────────────────────────

    @commands.command(name="purge", aliases=["clear", "clean"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge_cmd(self, ctx: commands.Context, amount: int = 10):
        """Bulk delete messages (1–100)."""
        amount = max(1, min(amount, 100))
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(embed=success(f"Deleted **{len(deleted)}** message(s)."))
        import asyncio
        await asyncio.sleep(4)
        await msg.delete()

    # ── !slowmode ─────────────────────────────────────────────────────────────

    @commands.command(name="slowmode", aliases=["slow"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def slowmode_cmd(self, ctx: commands.Context, seconds: int = 0):
        """Set channel slowmode in seconds (0 to disable)."""
        await ctx.channel.edit(slowmode_delay=max(0, min(seconds, 21600)))
        msg = f"Slowmode set to **{seconds}s**" if seconds else "Slowmode **disabled**"
        await ctx.reply(embed=success(msg), mention_author=False)

    # ── !lock / !unlock ───────────────────────────────────────────────────────

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock_cmd(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Lock a channel so members can't send messages."""
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.reply(embed=success(f"🔒 Locked {ch.mention}"), mention_author=False)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock_cmd(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unlock a channel."""
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.reply(embed=success(f"🔓 Unlocked {ch.mention}"), mention_author=False)

    # ── Slash Commands ────────────────────────────────────────────────────────

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not member.guild_permissions.ban_members or not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(embed=error("Missing permissions."), ephemeral=True)
        await member.ban(reason=reason)
        await interaction.response.send_message(embed=success(f"Banned **{member}** — {reason}"))

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await interaction.response.send_message(embed=success(f"Kicked **{member}** — {reason}"))

    @app_commands.command(name="mute", description="Timeout a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def slash_mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int = 10, reason: str = "No reason provided"):
        import datetime
        await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(embed=success(f"Muted **{member}** for **{minutes}m** — {reason}"))

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def slash_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        count = await add_warning(interaction.guild.id, member.id, interaction.user.id, reason)
        await interaction.response.send_message(embed=warn(f"Warned **{member}** — {reason}\nTotal warnings: **{count}**"))

    @app_commands.command(name="purge", description="Bulk delete messages")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def slash_purge(self, interaction: discord.Interaction, amount: int = 10):
        amount = max(1, min(amount, 100))
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(embed=success(f"Deleted **{len(deleted)}** message(s)."), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
