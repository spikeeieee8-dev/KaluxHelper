import discord
from discord.ext import commands
import aiosqlite
import re
from main.config import DB_PATH, COLOR_ERROR

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Simple regex for Discord invite links
        self.invite_regex = re.compile(r"(discord(?:\.gg|app\.com/invite)/[\w-]{2,})")

    async def cog_load(self):
        """Initialize Auto-Mod settings table."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS automod_settings (
                    guild_id TEXT PRIMARY KEY,
                    banned_words TEXT DEFAULT '',
                    filter_links INTEGER DEFAULT 0,
                    max_mentions INTEGER DEFAULT 5
                )
            """)
            await db.commit()

    async def get_settings(self, guild_id):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT banned_words, filter_links, max_mentions FROM automod_settings WHERE guild_id = ?", (str(guild_id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"words": row[0].split(","), "links": bool(row[1]), "mentions": row[2]}
                return {"words": [], "links": False, "mentions": 5}

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        """🛡️ AutoMod Configuration Hub"""
        await ctx.send("Usage: `!automod addword <word>`, `!automod togglelinks`, `!automod setmentions <num>`")

    @automod.command()
    async def addword(self, ctx, word: str):
        """🚫 Add a word to the blacklist"""
        settings = await self.get_settings(ctx.guild.id)
        words = settings["words"]
        if word.lower() not in words:
            words.append(word.lower())
            new_list = ",".join(filter(None, words))
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("INSERT INTO automod_settings (guild_id, banned_words) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET banned_words = ?", (str(ctx.guild.id), new_list, new_list))
                await db.commit()
            await ctx.send(f"✅ Added `{word}` to the blacklist.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.author.guild_permissions.manage_messages:
            return

        settings = await self.get_settings(message.guild.id)
        content = message.content.lower()

        # 1. Banned Words Check
        if any(word in content for word in settings["words"] if word):
            await message.delete()
            return await message.channel.send(f"⚠️ {message.author.mention}, that word is not allowed here!", delete_after=5)

        # 2. Invite Link Filter
        if settings["links"] and self.invite_regex.search(content):
            await message.delete()
            return await message.channel.send(f"🚫 {message.author.mention}, invite links are forbidden!", delete_after=5)

        # 3. Anti-Mention Raid
        if len(message.mentions) > settings["mentions"]:
            await message.delete()
            return await message.channel.send(f"🛡️ {message.author.mention}, too many mentions! Relax.", delete_after=5)

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
