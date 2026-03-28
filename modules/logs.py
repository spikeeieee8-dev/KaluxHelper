import discord
from discord.ext import commands
import aiosqlite
import datetime
from main.config import DB_PATH, COLOR_WARN, COLOR_ERROR, COLOR_INFO, COLOR_SUCCESS

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Initialize the log settings table in the database."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS log_settings (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT
                )
            """)
            await db.commit()

    async def get_log_channel(self, guild):
        """Retrieve the saved log channel from the database."""
        if not guild: return None
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT channel_id FROM log_settings WHERE guild_id = ?", (str(guild.id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return guild.get_channel(int(row[0]))
        return None

    @commands.command(name="setlogs")
    @commands.has_permissions(administrator=True)
    async def set_logs(self, ctx, channel: discord.TextChannel):
        """📌 Set the channel where all server logs will be sent."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO log_settings (guild_id, channel_id) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id
            """, (str(ctx.guild.id), str(channel.id)))
            await db.commit()
        await ctx.send(f"✅ **Log channel has been set to:** {channel.mention}")

    # ─── Message Logs ─────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        log_channel = await self.get_log_channel(message.guild)
        if not log_channel: return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {message.content or '[No text content]'}",
            color=COLOR_ERROR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text=f"User ID: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild: return
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel: return

        embed = discord.Embed(
            title="✏️ Message Edited",
            description=f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n\n**Before:** {before.content}\n**After:** {after.content}",
            color=COLOR_WARN,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text=f"User ID: {before.author.id}")
        await log_channel.send(embed=embed)

    # ─── Member & Moderation Logs ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel: return
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} joined the server.\n**Account Created:** <t:{int(member.created_at.timestamp())}:R>",
            color=COLOR_SUCCESS,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel: return
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"{member.mention} ({member.name}) has left or was kicked.",
            color=COLOR_ERROR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        log_channel = await self.get_log_channel(guild)
        if not log_channel: return
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**User:** {user.mention} ({user.name}) was banned.",
            color=COLOR_ERROR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

    # ─── Channel & Server Logs ────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel: return
        embed = discord.Embed(
            title="📂 Channel Created",
            description=f"**Name:** {channel.name}\n**Type:** {channel.type}",
            color=COLOR_SUCCESS,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel: return
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"**Name:** {channel.name}",
            color=COLOR_ERROR,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log_channel = await self.get_log_channel(role.guild)
        if not log_channel: return
        embed = discord.Embed(
            title="🛡️ Role Created",
            description=f"**Name:** {role.name}",
            color=COLOR_INFO,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
