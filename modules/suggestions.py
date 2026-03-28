import discord
from discord.ext import commands
import aiosqlite
from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, error

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_channel_id = None

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            # Table for the suggestions themselves
            await db.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    message_id TEXT PRIMARY KEY,
                    author_id TEXT,
                    content TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            """)
            # Table to track individual user votes to prevent duplicates/spam
            await db.execute("""
                CREATE TABLE IF NOT EXISTS suggestion_votes (
                    message_id TEXT,
                    user_id TEXT,
                    vote_type TEXT,
                    PRIMARY KEY (message_id, user_id)
                )
            """)
            await db.commit()

    @commands.command(name="setsuggest")
    @commands.has_permissions(manage_guild=True)
    async def set_suggest_channel(self, ctx):
        self.suggestion_channel_id = ctx.channel.id
        await ctx.send(embed=success(f"Suggestions moved to {ctx.channel.mention}"))

    @commands.command(name="suggest")
    @commands.cooldown(1, 300, commands.BucketType.user) # 5-minute cooldown to prevent flooding
    async def suggest(self, ctx, *, text: str):
        if not self.suggestion_channel_id:
            return await ctx.send(embed=error("Staff must run `!setsuggest` first."))

        channel = self.bot.get_channel(self.suggestion_channel_id)
        embed = discord.Embed(title="💡 New Suggestion", description=text, color=COLOR_BRAND)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Votes", value="👍 0 | 👎 0", inline=False)
        embed.set_footer(text="Click below to vote. You can change or remove your vote at any time.")

        view = SuggestionView(self.bot)
        msg = await channel.send(embed=embed, view=view)
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO suggestions (message_id, author_id, content) VALUES (?, ?, ?)",
                             (str(msg.id), str(ctx.author.id), text))
            await db.commit()

        await ctx.message.delete()
        await ctx.send(f"✅ Suggestion submitted in <#{self.suggestion_channel_id}>.", delete_after=5)

class SuggestionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def update_counts(self, message_id):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT vote_type, COUNT(*) FROM suggestion_votes WHERE message_id = ? GROUP BY vote_type", (str(message_id),)) as cursor:
                counts = {row[0]: row[1] for row in await cursor.fetchall()}
                return counts.get('up', 0), counts.get('down', 0)

    async def handle_vote(self, interaction: discord.Interaction, vote_type: str):
        msg_id = str(interaction.message.id)
        user_id = str(interaction.user.id)

        async with aiosqlite.connect(DB_PATH) as db:
            # Check for existing vote
            async with db.execute("SELECT vote_type FROM suggestion_votes WHERE message_id = ? AND user_id = ?", (msg_id, user_id)) as cursor:
                existing_vote = await cursor.fetchone()

            if existing_vote:
                if existing_vote[0] == vote_type:
                    # Same vote clicked again -> Remove it
                    await db.execute("DELETE FROM suggestion_votes WHERE message_id = ? AND user_id = ?", (msg_id, user_id))
                    action = "removed"
                else:
                    # Opposite vote clicked -> Switch it
                    await db.execute("UPDATE suggestion_votes SET vote_type = ? WHERE message_id = ? AND user_id = ?", (vote_type, msg_id, user_id))
                    action = "switched"
            else:
                # New vote
                await db.execute("INSERT INTO suggestion_votes (message_id, user_id, vote_type) VALUES (?, ?, ?)", (msg_id, user_id, vote_type))
                action = "added"
            
            await db.commit()

        # Update the original embed
        up, down = await self.update_counts(msg_id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Votes", value=f"👍 **{up}** | 👎 **{down}**", inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Upvote", style=discord.ButtonStyle.success, custom_id="suggest_up", emoji="👍")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, 'up')

    @discord.ui.button(label="Downvote", style=discord.ButtonStyle.danger, custom_id="suggest_down", emoji="👎")
    async def downvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, 'down')

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
