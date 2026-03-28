import discord
from discord.ext import commands, tasks
import aiosqlite
import random
import datetime
from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, error, brand

class GiveawayView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.success, emoji="🎉", custom_id="enter_gaw")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg_id = str(interaction.message.id)
        user_id = str(interaction.user.id)

        async with aiosqlite.connect(DB_PATH) as db:
            # 1. Check if already entered
            async with db.execute("SELECT 1 FROM giveaway_entries WHERE message_id = ? AND user_id = ?", (msg_id, user_id)) as cursor:
                if await cursor.fetchone():
                    return await interaction.response.send_message("❌ You've already entered!", ephemeral=True)
            
            # 2. Add entry
            await db.execute("INSERT INTO giveaway_entries (message_id, user_id) VALUES (?, ?)", (msg_id, user_id))
            
            # 3. Get new total count
            async with db.execute("SELECT COUNT(*) FROM giveaway_entries WHERE message_id = ?", (msg_id,)) as count_cursor:
                count_row = await count_cursor.fetchone()
                count = count_row[0]
            
            await db.commit()

        # 4. Update the Embed with the new count
        embed = interaction.message.embeds[0]
        # We assume the 'Entries' field is at index 1
        embed.set_field_at(1, name="📈 Entries", value=f"**{count}** Users", inline=True)
        await interaction.response.edit_message(embed=embed)
        
        # Send a private confirmation
        await interaction.followup.send(f"✅ Success! You are now in the draw for the prize.", ephemeral=True)

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    message_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    prize TEXT,
                    end_time TIMESTAMP,
                    winner_count INTEGER,
                    active INTEGER DEFAULT 1
                )
            """)
            await db.execute("CREATE TABLE IF NOT EXISTS giveaway_entries (message_id TEXT, user_id TEXT)")
            await db.commit()

    @tasks.loop(seconds=20)
    async def check_giveaways(self):
        now = datetime.datetime.now()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT message_id, channel_id, prize, winner_count FROM giveaways WHERE end_time <= ? AND active = 1", (now,)) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    await self.end_giveaway(row[0], row[1], row[2], row[3])

    async def end_giveaway(self, msg_id, chan_id, prize, winners_count):
        channel = self.bot.get_channel(int(chan_id))
        if not channel: return

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM giveaway_entries WHERE message_id = ?", (msg_id,)) as cursor:
                entries = [row[0] for row in await cursor.fetchall()]
            
            await db.execute("UPDATE giveaways SET active = 0 WHERE message_id = ?", (msg_id,))
            await db.commit()

        try:
            msg = await channel.fetch_message(int(msg_id))
            embed = msg.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "🎁 Giveaway Ended"
            embed.description = f"**Prize:** {prize}\n**Status:** Closed"
            
            if not entries:
                embed.set_field_at(0, name="Winner(s)", value="No entries found.", inline=False)
                await msg.edit(embed=embed, view=None)
                return await channel.send(f"⚠️ The giveaway for **{prize}** ended with no participants.")

            winners = random.sample(entries, min(len(entries), winners_count))
            winner_mentions = ", ".join([f"<@{w}>" for w in winners])

            embed.set_field_at(0, name="🏆 Winner(s)", value=winner_mentions, inline=False)
            await msg.edit(embed=embed, view=None)
            await channel.send(f"🎊 Congratulations {winner_mentions}! You won **{prize}**!")
        except:
            pass

    @commands.command(name="gstart")
    @commands.has_permissions(manage_guild=True)
    async def start_giveaway(self, ctx, time_str: str, winners: int, *, prize: str):
        """!gstart 10m 1 Discord Nitro"""
        seconds = 0
        t = time_str.lower()
        if t.endswith("s"): seconds = int(t[:-1])
        elif t.endswith("m"): seconds = int(t[:-1]) * 60
        elif t.endswith("h"): seconds = int(t[:-1]) * 3600
        elif t.endswith("d"): seconds = int(t[:-1]) * 86400
        
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        unix_end = int(end_time.timestamp())

        embed = discord.Embed(
            title="🎁 KaluxHost | Active Giveaway",
            description=f"We are giving away **{prize}**!\nClick the button below to join.",
            color=COLOR_BRAND
        )
        embed.add_field(name="⏳ Ends In", value=f"<t:{unix_end}:R> (<t:{unix_end}:f>)", inline=False)
        embed.add_field(name="📈 Entries", value="**0** Users", inline=True)
        embed.add_field(name="👥 Winners", value=f"**{winners}**", inline=True)
        embed.set_footer(text="Good luck to everyone! | Powered by KaluxHost")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

        view = GiveawayView(self.bot)
        msg = await ctx.send(embed=embed, view=view)
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO giveaways (message_id, channel_id, prize, end_time, winner_count) VALUES (?, ?, ?, ?, ?)",
                             (str(msg.id), str(ctx.channel.id), prize, end_time, winners))
            await db.commit()
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
