"""
HOSTING MODULE — KaluxHost Themed
Commands: plans, uptime, status, support, ticket, node
Both prefix and slash variants.
"""
import datetime
import discord
from discord import app_commands
from discord.ext import commands

from main.config import COLOR_BRAND, BOT_NAME
from main.utils.embeds import brand, success, warn


PLANS = [
    {"name": "⚡ Starter",   "ram": "2 GB",  "cpu": "1 vCore",   "storage": "20 GB SSD",  "price": "$2.99/mo", "color": 0x57F287},
    {"name": "🚀 Pro",       "ram": "4 GB",  "cpu": "2 vCores",  "storage": "50 GB SSD",  "price": "$5.99/mo", "color": COLOR_BRAND},
    {"name": "💎 Elite",     "ram": "8 GB",  "cpu": "4 vCores",  "storage": "100 GB SSD", "price": "$9.99/mo", "color": 0xFEE75C},
    {"name": "👑 Dedicated", "ram": "16 GB+","cpu": "8+ vCores", "storage": "250 GB SSD", "price": "Custom",   "color": 0xED4245},
]

SERVICES = [
    ("🟢", "Web Panel"),
    ("🟢", "Game Servers"),
    ("🟢", "VPS / VDS Nodes"),
    ("🟢", "Discord Bot"),
    ("🟢", "Billing System"),
    ("🟢", "DDoS Protection"),
]


def _plans_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🖥️ KaluxHost — Hosting Plans",
        description="Premium hosting with **99.9% uptime guarantee**.\nAll plans include DDoS protection & 24/7 support.",
        color=COLOR_BRAND,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    for p in PLANS:
        embed.add_field(
            name=p["name"],
            value=f"RAM: `{p['ram']}`\nCPU: `{p['cpu']}`\nDisk: `{p['storage']}`\nPrice: **{p['price']}**",
            inline=True,
        )
    embed.set_footer(text=f"{BOT_NAME} | Visit our website to order!")
    return embed


def _status_embed() -> discord.Embed:
    embed = brand("📊 KaluxHost — Service Status")
    embed.description = "\n".join(f"{icon} **{name}** — Operational" for icon, name in SERVICES)
    return embed


class Hosting(commands.Cog, name="Hosting"):
    """🖥️ KaluxHost hosting commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !plans ────────────────────────────────────────────────────────────────

    @commands.command(name="plans", aliases=["pricing", "packages"])
    async def plans_cmd(self, ctx: commands.Context):
        """View KaluxHost hosting plans."""
        await ctx.reply(embed=_plans_embed(), mention_author=False)

    # ── !status ───────────────────────────────────────────────────────────────

    @commands.command(name="status", aliases=["services"])
    async def status_cmd(self, ctx: commands.Context):
        """Check KaluxHost service status."""
        await ctx.reply(embed=_status_embed(), mention_author=False)

    # ── !uptime ───────────────────────────────────────────────────────────────

    @commands.command(name="uptime")
    async def uptime_cmd(self, ctx: commands.Context):
        """Check bot and service uptime."""
        delta   = datetime.timedelta(milliseconds=round(self.bot.latency * 1000))
        uptime  = datetime.datetime.now(datetime.timezone.utc) - self.bot.start_time
        embed   = brand("📡 Uptime Status")
        embed.add_field(name="🤖 Bot Online Since", value=f"<t:{int(self.bot.start_time.timestamp())}:R>", inline=True)
        embed.add_field(name="📶 API Latency",       value=f"`{round(self.bot.latency*1000)}ms`",           inline=True)
        embed.add_field(name="🟢 Services",           value="All systems operational",                      inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    # ── !support ──────────────────────────────────────────────────────────────

    @commands.command(name="support", aliases=["help-host"])
    async def support_cmd(self, ctx: commands.Context):
        """Get support information."""
        embed = brand("🎫 KaluxHost Support")
        embed.add_field(name="📩 Open a Ticket",  value="Use `!ticket` or `/ticket` to open a ticket",  inline=False)
        embed.add_field(name="💬 Discord",         value="Message a staff member",              inline=True)
        embed.add_field(name="📧 Email",            value="support@kaluxhost.com",              inline=True)
        embed.add_field(name="⏱️ Response Time",   value="Usually within 1 hour",              inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    # ── !node ─────────────────────────────────────────────────────────────────

    @commands.command(name="node", aliases=["nodes", "network"])
    async def node_cmd(self, ctx: commands.Context):
        """Show KaluxHost node/network information."""
        embed = brand("🌐 KaluxHost Network")
        nodes = [
            ("🇺🇸 US-East",    "New York",       "Online"),
            ("🇺🇸 US-West",    "Los Angeles",    "Online"),
            ("🇩🇪 EU-Central", "Frankfurt",      "Online"),
            ("🇸🇬 AP-Southeast","Singapore",     "Online"),
        ]
        for flag, loc, status in nodes:
            embed.add_field(name=f"{flag} {loc}", value=f"Status: 🟢 {status}", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    # ── Slash Commands ────────────────────────────────────────────────────────

    @app_commands.command(name="plans", description="View KaluxHost hosting plans")
    async def slash_plans(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=_plans_embed())

    @app_commands.command(name="status", description="Check KaluxHost service status")
    async def slash_status(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=_status_embed())

    @app_commands.command(name="uptime", description="Check bot uptime and latency")
    async def slash_uptime(self, interaction: discord.Interaction):
        embed = brand("📡 Uptime Status")
        embed.add_field(name="🤖 Bot Online Since", value=f"<t:{int(self.bot.start_time.timestamp())}:R>", inline=True)
        embed.add_field(name="📶 API Latency",       value=f"`{round(self.bot.latency*1000)}ms`",           inline=True)
        embed.add_field(name="🟢 Services",           value="All systems operational",                      inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    # Track start time for uptime command
    import datetime
    bot.start_time = getattr(bot, "start_time", datetime.datetime.now(datetime.timezone.utc))
    await bot.add_cog(Hosting(bot))
