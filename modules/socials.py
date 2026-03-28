import discord
from discord.ext import commands
import aiosqlite
from main.config import DB_PATH, COLOR_INFO, COLOR_SUCCESS

class Socials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Mapping for clean display names and common emojis
        self.icons = {
            "youtube": "🔴",
            "instagram": "📸",
            "tiktok": "📱",
            "linkedin": "💼",
            "twitter": "🐦",
            "x": "✖️",
            "facebook": "👥",
            "website": "🌐",
            "discord": "💬"
        }

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS social_links (
                    guild_id TEXT,
                    platform TEXT,
                    url TEXT,
                    PRIMARY KEY (guild_id, platform)
                )""")
            await db.commit()

    @commands.group(invoke_without_command=True)
    async def socials(self, ctx):
        """📱 Show all KaluxHost official social media links."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT platform, url FROM social_links WHERE guild_id = ?", (str(ctx.guild.id),)) as cursor:
                links = await cursor.fetchall()

        if not links:
            return await ctx.send("ℹ️ No social links set. Admins use `!socials set <platform> <url>`.")

        embed = discord.Embed(
            title="🔗 KaluxHost Official Socials",
            description="Follow us to stay updated on our hosting services!",
            color=COLOR_INFO
        )
        
        # Build the list of links
        social_list = ""
        for platform, url in links:
            icon = self.icons.get(platform.lower(), "🔗")
            social_list += f"{icon} **{platform.title()}:** [Click Here to Visit]({url})\n"
        
        embed.add_field(name="Our Platforms", value=social_list, inline=False)
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

    @socials.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_social(self, ctx, platform: str, url: str):
        """🔗 Add a social (e.g., !socials set TikTok https://...)"""
        if not url.startswith("http"):
            return await ctx.send("❌ Please provide a valid URL (starting with http/https).")

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO social_links (guild_id, platform, url) 
                VALUES (?, ?, ?) 
                ON CONFLICT(guild_id, platform) DO UPDATE SET url = excluded.url
            """, (str(ctx.guild.id), platform.lower(), url))
            await db.commit()

        await ctx.send(f"✅ **{platform.title()}** link has been updated!")

    @socials.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_social(self, ctx, platform: str):
        """🗑️ Remove a social link (e.g., !socials remove Insta)"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM social_links WHERE guild_id = ? AND platform = ?", (str(ctx.guild.id), platform.lower()))
            await db.commit()
        await ctx.send(f"🗑️ Removed **{platform.title()}** from socials.")

async def setup(bot):
    await bot.add_cog(Socials(bot))
