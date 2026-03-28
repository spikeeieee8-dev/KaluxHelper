import discord
from discord.ext import commands
import aiosqlite
from main.config import DB_PATH

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Initialize the counting table in your database."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS counting_game (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    current_count INTEGER DEFAULT 0,
                    last_user_id TEXT,
                    high_score INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    @commands.command(name="setcounting")
    @commands.has_permissions(administrator=True)
    async def set_counting(self, ctx, channel: discord.TextChannel):
        """📌 Set the channel for the counting game."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO counting_game (guild_id, channel_id, current_count, high_score)
                VALUES (?, ?, 0, 0)
                ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id
            """, (str(ctx.guild.id), str(channel.id)))
            await db.commit()
        await ctx.send(f"✅ **Counting channel set to:** {channel.mention}. Start with **1**!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Check if this is the counting channel
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT channel_id, current_count, last_user_id, high_score FROM counting_game WHERE guild_id = ?", (str(message.guild.id),)) as cursor:
                row = await cursor.fetchone()
        
        if not row or str(message.channel.id) != row[0]:
            return

        # Try to see if the message is a number
        try:
            content = message.content.split()[0] # Take first word only
            user_count = int(content)
        except (ValueError, IndexError):
            return # Ignore non-numeric talk

        expected_count = row[1] + 1
        last_user = row[2]
        high_score = row[3]

        # Rule 1: Correct Number
        # Rule 2: Different User
        if user_count != expected_count or str(message.author.id) == last_user:
            # RESET!
            reason = "Wrong number!" if user_count != expected_count else "You can't count twice in a row!"
            await message.add_reaction("❌")
            await message.channel.send(f"💥 **{message.author.display_name}** ruined it! {reason}\n**Next number is 1.** (High Score: {high_score})")
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE counting_game SET current_count = 0, last_user_id = NULL WHERE guild_id = ?", (str(message.guild.id),))
                await db.commit()
        else:
            # SUCCESS!
            await message.add_reaction("✅")
            new_high_score = max(high_score, user_count)
            
            if user_count > high_score:
                await message.add_reaction("🏆")

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("""
                    UPDATE counting_game 
                    SET current_count = ?, last_user_id = ?, high_score = ? 
                    WHERE guild_id = ?
                """, (user_count, str(message.author.id), new_high_score, str(message.guild.id)))
                await db.commit()

async def setup(bot):
    await bot.add_cog(Counting(bot))
