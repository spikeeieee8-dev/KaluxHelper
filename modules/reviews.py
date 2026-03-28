import discord
from discord.ext import commands
import aiosqlite
from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, error, brand

class Reviews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vouch_channel_id = None # Set via !setvouch

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    rating INTEGER,
                    comment TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    @commands.command(name="setvouch")
    @commands.has_permissions(manage_guild=True)
    async def set_vouch_channel(self, ctx):
        """Sets the channel where public vouches are posted."""
        self.vouch_channel_id = ctx.channel.id
        await ctx.send(embed=success(f"Vouches will now be posted in {ctx.channel.mention}"))

    @commands.command(name="vouch")
    @commands.cooldown(1, 3600, commands.BucketType.user) # 1 vouch per hour to prevent spam
    async def vouch(self, ctx, rating: int, *, comment: str):
        """
        Leave a review for KaluxHost.
        Usage: !vouch 5 Best VPS I've ever used!
        """
        if not self.vouch_channel_id:
            return await ctx.send(embed=error("Staff must set the vouch channel first using `!setvouch`."))

        if not (1 <= rating <= 5):
            return await ctx.send(embed=error("Rating must be between 1 and 5 stars."))

        # Create the public vouch embed
        stars = "⭐" * rating
        vouch_channel = self.bot.get_channel(self.vouch_channel_id)
        
        embed = discord.Embed(title="💎 New Verified Vouch", color=0xFFD700) # Gold color
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Rating", value=stars, inline=True)
        embed.add_field(name="Review", value=comment, inline=False)
        embed.set_footer(text=f"Verified Customer | {ctx.author.id}")
        embed.set_thumbnail(url="https://i.imgur.com/8Q9X6X8.png") # Optional: Add a 'Verified' badge URL here

        await vouch_channel.send(embed=embed)
        
        # Save to database for future leaderboards or stats
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO reviews (user_id, rating, comment) VALUES (?, ?, ?)",
                             (str(ctx.author.id), rating, comment))
            await db.commit()

        await ctx.send(embed=success("Thank you for your vouch! It has been posted."), delete_after=5)
        await ctx.message.delete()

    @commands.command(name="vouchstats")
    async def vouch_stats(self, ctx):
        """Shows the average rating for KaluxHost."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT AVG(rating), COUNT(*) FROM reviews") as cursor:
                row = await cursor.fetchone()
                if not row or row[1] == 0:
                    return await ctx.send(embed=brand("Stats", "No reviews yet!"))
                
                avg = round(row[0], 1)
                total = row[1]
                await ctx.send(embed=brand("KaluxHost Trust Score", f"Average: **{avg}/5** ⭐\nTotal Vouches: **{total}**"))

async def setup(bot):
    await bot.add_cog(Reviews(bot))
