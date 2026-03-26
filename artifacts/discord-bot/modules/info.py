"""
INFO MODULE
Commands: help, ping, serverinfo, userinfo, botinfo
Both prefix and slash variants.
"""
import discord
from discord import app_commands
from discord.ext import commands
import datetime

from main.config import BOT_NAME, BOT_VERSION, COLOR_BRAND
from main.utils.database import get_prefix
from main.utils.embeds import brand, error


class Info(commands.Cog, name="Info"):
    """ℹ️ General info commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !help ─────────────────────────────────────────────────────────────────

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_cmd(self, ctx: commands.Context, *, module: str = None):
        """Show all commands, or commands for a specific module."""
        prefix = await get_prefix(ctx.guild.id) if ctx.guild else "!"

        if module:
            cog = self.bot.get_cog(module.title())
            if not cog:
                return await ctx.reply(embed=error(f"Module `{module}` not found."), mention_author=False)
            cmds = [c for c in cog.get_commands() if not c.hidden]
            embed = brand(f"📦 {cog.qualified_name} — Commands")
            embed.description = "\n".join(
                f"`{prefix}{c.name}` — {c.brief or c.description or 'No description'}"
                for c in cmds
            ) or "No commands."
            return await ctx.reply(embed=embed, mention_author=False)

        embed = discord.Embed(
            title=f"📖 {BOT_NAME} Bot — Help",
            description=(
                f"Use `{prefix}<command>` **or** `/<command>` to run commands.\n"
                f"Use `{prefix}help <module>` for module-specific help."
            ),
            color=COLOR_BRAND,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        for cog_name, cog in sorted(self.bot.cogs.items()):
            cmds = [c for c in cog.get_commands() if not c.hidden]
            if not cmds:
                continue
            embed.add_field(
                name=f"{cog.description.split()[0] if cog.description else '📦'} {cog_name}",
                value=" ".join(f"`{prefix}{c.name}`" for c in cmds),
                inline=False,
            )

        embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} | Prefix: {prefix}")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !ping ─────────────────────────────────────────────────────────────────

    @commands.command(name="ping")
    async def ping_cmd(self, ctx: commands.Context):
        """Check bot latency."""
        ws  = round(self.bot.latency * 1000)
        msg = await ctx.reply("🏓 Calculating…", mention_author=False)
        rtt = round((msg.created_at - ctx.message.created_at).total_seconds() * 1000)
        embed = brand("🏓 Pong!")
        embed.add_field(name="WebSocket", value=f"`{ws}ms`", inline=True)
        embed.add_field(name="Round-Trip", value=f"`{rtt}ms`", inline=True)
        await msg.edit(content=None, embed=embed)

    # ── !serverinfo ───────────────────────────────────────────────────────────

    @commands.command(name="serverinfo", aliases=["server", "si", "guildinfo"])
    @commands.guild_only()
    async def serverinfo_cmd(self, ctx: commands.Context):
        """Show server information."""
        g = ctx.guild
        embed = brand(f"🏠 {g.name}")
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner",        value=f"<@{g.owner_id}>",       inline=True)
        embed.add_field(name="Members",      value=f"{g.member_count:,}",    inline=True)
        embed.add_field(name="Channels",     value=f"{len(g.channels)}",     inline=True)
        embed.add_field(name="Roles",        value=f"{len(g.roles)}",        inline=True)
        embed.add_field(name="Boost Level",  value=f"Level {g.premium_tier}",inline=True)
        embed.add_field(name="Created",      value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)
        embed.set_footer(text=f"ID: {g.id} | KaluxHost Bot")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !userinfo ─────────────────────────────────────────────────────────────

    @commands.command(name="userinfo", aliases=["user", "ui", "whois"])
    @commands.guild_only()
    async def userinfo_cmd(self, ctx: commands.Context, *, member: discord.Member = None):
        """Show user information."""
        m = member or ctx.author
        roles = [r.mention for r in reversed(m.roles) if r.name != "@everyone"][:10]
        embed = brand(f"👤 {m}")
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="ID",              value=m.id,                                         inline=True)
        embed.add_field(name="Nickname",        value=m.nick or "None",                             inline=True)
        embed.add_field(name="Bot?",            value="Yes" if m.bot else "No",                     inline=True)
        embed.add_field(name="Joined Server",   value=f"<t:{int(m.joined_at.timestamp())}:R>",     inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(m.created_at.timestamp())}:R>",    inline=True)
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) or "None",             inline=False)
        embed.set_footer(text=f"ID: {m.id} | KaluxHost Bot")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !botinfo ──────────────────────────────────────────────────────────────

    @commands.command(name="botinfo", aliases=["bot", "about"])
    async def botinfo_cmd(self, ctx: commands.Context):
        """Show bot information."""
        embed = brand(f"🤖 {BOT_NAME} Bot")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Version",   value=BOT_VERSION,                              inline=True)
        embed.add_field(name="Guilds",    value=f"{len(self.bot.guilds)}",                 inline=True)
        embed.add_field(name="Latency",   value=f"{round(self.bot.latency*1000)}ms",       inline=True)
        embed.add_field(name="Library",   value="discord.py 2.x",                         inline=True)
        embed.add_field(name="Language",  value="Python 3.12",                            inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    # ── Slash Commands ────────────────────────────────────────────────────────

    @app_commands.command(name="ping", description="Check bot latency")
    async def slash_ping(self, interaction: discord.Interaction):
        ws = round(self.bot.latency * 1000)
        embed = brand("🏓 Pong!")
        embed.add_field(name="WebSocket", value=f"`{ws}ms`", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Show server information")
    @app_commands.guild_only()
    async def slash_serverinfo(self, interaction: discord.Interaction):
        g = interaction.guild
        embed = brand(f"🏠 {g.name}")
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner",        value=f"<@{g.owner_id}>",       inline=True)
        embed.add_field(name="Members",      value=f"{g.member_count:,}",    inline=True)
        embed.add_field(name="Channels",     value=f"{len(g.channels)}",     inline=True)
        embed.add_field(name="Roles",        value=f"{len(g.roles)}",        inline=True)
        embed.add_field(name="Boost Level",  value=f"Level {g.premium_tier}",inline=True)
        embed.add_field(name="Created",      value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)
        embed.set_footer(text=f"ID: {g.id} | KaluxHost Bot")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show user information")
    @app_commands.guild_only()
    async def slash_userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        m = member or interaction.user
        roles = [r.mention for r in reversed(m.roles) if r.name != "@everyone"][:10]
        embed = brand(f"👤 {m}")
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="ID",              value=m.id,                                         inline=True)
        embed.add_field(name="Nickname",        value=m.nick or "None",                             inline=True)
        embed.add_field(name="Joined Server",   value=f"<t:{int(m.joined_at.timestamp())}:R>",     inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(m.created_at.timestamp())}:R>",    inline=True)
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) or "None",             inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
