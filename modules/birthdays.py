import discord
from discord.ext import commands, tasks
import aiosqlite
import datetime
from main.config import DB_PATH

class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start() # Start the daily background check

    async def cog_load(self):
        """Ensure the birthday table exists in your restored DB."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS birthdays (
                    user_id TEXT PRIMARY KEY,
                    birthday TEXT NOT NULL,
                    guild_id TEXT NOT NULL
                )
            """)
            await db.commit()

    @commands.command(name="setbirthday")
    async def set_birthday(self, ctx, date: str):
        """📅 Set your birthday (Format: DD/MM)"""
        try:
            # Validate format
            datetime.datetime.strptime(date, "%d/%m")
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO birthdays (user_id, birthday, guild_id) VALUES (?, ?, ?)",
                    (str(ctx.author.id), date, str(ctx.guild.id))
                )
                await db.commit()
            await ctx.send(f"✅ Saved! I'll remember your birthday on **{date}**.")
        except ValueError:
            await ctx.send("❌ Invalid format! Please use **DD/MM** (e.g., `!setbirthday 25/03`).")

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Checks every 24 hours if anyone has a birthday today."""
        now = datetime.datetime.now().strftime("%d/%m")
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, guild_id FROM birthdays WHERE birthday = ?", (now,)) as cursor:
                birthdays_today = await cursor.fetchall()

        for user_id, guild_id in birthdays_today:
            guild = self.bot.get_guild(int(guild_id))
            if not guild: continue
            
            # Find a 'general' or 'announcements' channel to post in
            channel = discord.utils.get(guild.text_channels, name="general") or guild.text_channels[0]
            
            embed = discord.Embed(
                title="🎂 Happy Birthday!",
                description=f"Today we celebrate <@{user_id}>! Hope you have an amazing day! 🎉",
                color=0xFEE75C
            )
            await channel.send(content=f"🎈 Attention <@{user_id}>!", embed=embed)

    @check_birthdays.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Birthdays(bot))
