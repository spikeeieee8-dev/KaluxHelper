import discord
from discord.ext import commands, tasks
import aiosqlite
from main.config import DB_PATH

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stat_channels (
                    guild_id TEXT,
                    channel_id TEXT,
                    stat_type TEXT,
                    PRIMARY KEY (guild_id, stat_type)
                )""")
            await db.commit()

    @tasks.loop(minutes=10)
    async def update_stats(self):
        """Update all registered stat channels every 10 minutes."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT guild_id, channel_id, stat_type FROM stat_channels") as cursor:
                rows = await cursor.fetchall()

        for g_id, c_id, s_type in rows:
            guild = self.bot.get_guild(int(g_id))
            if not guild: continue
            
            channel = guild.get_channel(int(c_id))
            if not channel: continue

            count = 0
            if s_type == "members":
                count = guild.member_count
            elif s_type == "humans":
                count = len([m for m in guild.members if not m.bot])
            elif s_type == "bots":
                count = len([m for m in guild.members if m.bot])

            new_name = f"📊 {s_type.title()}: {count}"
            if channel.name != new_name:
                try:
                    await channel.edit(name=new_name)
                except:
                    pass

    @commands.command(name="setupstats")
    @commands.has_permissions(administrator=True)
    async def setup_stats(self, ctx, stat_type: str):
        """📈 Setup a live counter. Types: members, humans, bots"""
        if stat_type.lower() not in ["members", "humans", "bots"]:
            return await ctx.send("❌ Invalid type. Use `members`, `humans`, or `bots`.")

        # Create a locked voice channel
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False)
        }
        channel = await ctx.guild.create_voice_channel(
            name=f"📊 {stat_type.title()}: ...",
            overwrites=overwrites,
            reason="Stats System Setup"
        )

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO stat_channels (guild_id, channel_id, stat_type) 
                VALUES (?, ?, ?) 
                ON CONFLICT(guild_id, stat_type) DO UPDATE SET channel_id = excluded.channel_id
            """, (str(ctx.guild.id), str(channel.id), stat_type.lower()))
            await db.commit()

        await ctx.send(f"✅ {stat_type.title()} counter created: {channel.mention}")

async def setup(bot):
    await bot.add_cog(ServerStats(bot))
