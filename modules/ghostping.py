import discord
from discord.ext import commands
import datetime
from main.config import COLOR_WARN, COLOR_ERROR

class GhostPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore bots and messages with no content
        if message.author.bot or not message.content:
            return

        # Check if the message contained a mention
        # (Users, Roles, or @everyone/@here)
        has_mention = (
            len(message.mentions) > 0 or 
            len(message.role_mentions) > 0 or 
            message.mention_everyone
        )

        if has_mention:
            # Create the 'Expose' Embed
            embed = discord.Embed(
                title="👻 GHOST PING DETECTED",
                description=(
                    f"**Author:** {message.author.mention} ({message.author.id})\n"
                    f"**Channel:** {message.channel.mention}\n\n"
                    f"**Content:**\n{message.content}"
                ),
                color=COLOR_WARN,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_footer(text="Message was deleted")
            
            # Send to the same channel to expose them
            await message.channel.send(embed=embed)

            # Optional: Also log it to your Guard logs if they exist
            # (Requires your get_guard_log helper from modules.guard)
            # await self.log_to_guard(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Detects if someone pings and then edits the mention out."""
        if before.author.bot: return

        # If 'before' had a mention but 'after' does not
        before_mentions = len(before.mentions) + len(before.role_mentions) + (1 if before.mention_everyone else 0)
        after_mentions = len(after.mentions) + len(after.role_mentions) + (1 if after.mention_everyone else 0)

        if before_mentions > after_mentions:
            embed = discord.Embed(
                title="👻 GHOST PING (EDITED)",
                description=(
                    f"**Author:** {before.author.mention}\n"
                    f"**Original Content:**\n{before.content}\n\n"
                    f"**New Content:**\n{after.content}"
                ),
                color=COLOR_WARN,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await before.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GhostPing(bot))
