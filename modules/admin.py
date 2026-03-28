"""
ADMIN MODULE
Commands: setprefix, prefix, say, embed, announce
Server configuration and admin utilities.
"""
import discord
from discord import app_commands
from discord.ext import commands

from main.config import DEFAULT_PREFIX
from main.utils.database import get_prefix, set_prefix
from main.utils.embeds import success, error, brand


class Admin(commands.Cog, name="Admin"):
    """⚙️ Server admin and configuration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !setprefix ────────────────────────────────────────────────────────────

    @commands.command(name="setprefix", aliases=["changeprefix"])
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def setprefix_cmd(self, ctx: commands.Context, new_prefix: str):
        """Change the command prefix for this server."""
        if len(new_prefix) > 5:
            return await ctx.reply(embed=error("Prefix must be 5 characters or fewer."), mention_author=False)
        await set_prefix(ctx.guild.id, new_prefix)
        await ctx.reply(
            embed=success(f"Prefix changed to `{new_prefix}`\nTry it: `{new_prefix}help`"),
            mention_author=False,
        )

    # ── !prefix ───────────────────────────────────────────────────────────────

    @commands.command(name="prefix", aliases=["currentprefix", "myprefix"])
    @commands.guild_only()
    async def prefix_cmd(self, ctx: commands.Context):
        """Show the current prefix."""
        p = await get_prefix(ctx.guild.id)
        await ctx.reply(embed=brand("📌 Current Prefix", f"This server's prefix is `{p}`"), mention_author=False)

    # ── !say ──────────────────────────────────────────────────────────────────

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def say_cmd(self, ctx: commands.Context, *, message: str):
        """Make the bot say something."""
        await ctx.message.delete()
        await ctx.send(message)

    # ── !announce ─────────────────────────────────────────────────────────────

    @commands.command(name="announce", aliases=["announcement"])
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def announce_cmd(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """Send an announcement embed to a channel."""
        embed = brand("📢 Announcement", message)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        await channel.send(embed=embed)
        await ctx.reply(embed=success(f"Announcement sent to {channel.mention}"), mention_author=False)

    # ── Slash Commands ────────────────────────────────────────────────────────

    @app_commands.command(name="setprefix", description="Change the command prefix for this server")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def slash_setprefix(self, interaction: discord.Interaction, prefix: str):
        if len(prefix) > 5:
            return await interaction.response.send_message(embed=error("Prefix must be 5 characters or fewer."), ephemeral=True)
        await set_prefix(interaction.guild.id, prefix)
        await interaction.response.send_message(embed=success(f"Prefix changed to `{prefix}`\nTry it: `{prefix}help`"))

    @app_commands.command(name="prefix", description="Show the current command prefix")
    @app_commands.guild_only()
    async def slash_prefix(self, interaction: discord.Interaction):
        p = await get_prefix(interaction.guild.id)
        await interaction.response.send_message(embed=brand("📌 Current Prefix", f"This server's prefix is `{p}`"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
