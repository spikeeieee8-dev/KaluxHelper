import discord
from discord.ext import commands
import aiosqlite

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_limit = 3 
        self.db_path = "bot_data.db"

    async def cog_load(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Table for settings (Channel ID)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS starboard_config (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER
                )
            """)
            # Table for message tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS starboard_messages (
                    original_msg_id INTEGER PRIMARY KEY,
                    starboard_msg_id INTEGER
                )
            """)
            await db.commit()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setstarboard(self, ctx, channel: discord.TextChannel):
        """📌 Set the channel where starred messages will appear."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO starboard_config (guild_id, channel_id) VALUES (?, ?)", 
                             (ctx.guild.id, channel.id))
            await db.commit()
        await ctx.send(f"✅ **Starboard channel set to:** {channel.mention}")

    async def get_starboard_channel(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id FROM starboard_config WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "⭐":
            return

        # Get the configured channel ID from DB
        starboard_channel_id = await self.get_starboard_channel(payload.guild_id)
        if not starboard_channel_id or payload.channel_id == starboard_channel_id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        if message.author.bot:
            return

        reaction = discord.utils.get(message.reactions, emoji="⭐")
        if reaction and reaction.count >= self.star_limit:
            starboard_channel = self.bot.get_channel(starboard_channel_id)
            if starboard_channel:
                await self.send_to_starboard(message, reaction.count, starboard_channel)

    async def send_to_starboard(self, message, count, starboard_channel):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT starboard_msg_id FROM starboard_messages WHERE original_msg_id = ?", (message.id,)) as cursor:
                row = await cursor.fetchone()

            embed = discord.Embed(description=message.content, color=0xffac33, timestamp=message.created_at)
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Source", value=f"[Jump to Message]({message.jump_url})")
            
            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            content = f"⭐ **{count}** | {message.channel.mention}"

            if row:
                try:
                    star_msg = await starboard_channel.fetch_message(row[0])
                    await star_msg.edit(content=content, embed=embed)
                except discord.NotFound:
                    pass # Message was deleted from starboard
            else:
                new_star_msg = await starboard_channel.send(content=content, embed=embed)
                await db.execute("INSERT INTO starboard_messages (original_msg_id, starboard_msg_id) VALUES (?, ?)", 
                                 (message.id, new_star_msg.id))
                await db.commit()

async def setup(bot):
    await bot.add_cog(Starboard(bot))
