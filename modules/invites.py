import discord
from discord.ext import commands
import aiosqlite
from main.config import DB_PATH

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {} # guild_id: {code: uses}

    async def cog_load(self):
        """Initialize the invite tracking table."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS invite_stats (
                    guild_id TEXT,
                    inviter_id TEXT,
                    joins INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, inviter_id)
                )
            """)
            await db.commit()
        
        # Initial cache of all invites
        for guild in self.bot.guilds:
            try:
                self.invite_cache[guild.id] = {i.code: i.uses for i in await guild.invites()}
            except:
                continue

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if not guild.me.guild_permissions.manage_guild:
            return

        old_invites = self.invite_cache.get(guild.id, {})
        new_invites = await guild.invites()
        
        # Update cache and find the inviter
        inviter = None
        for invite in new_invites:
            if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                inviter = invite.inviter
                break
            old_invites[invite.code] = invite.uses
        
        self.invite_cache[guild.id] = old_invites

        if inviter and not inviter.bot:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("""
                    INSERT INTO invite_stats (guild_id, inviter_id, joins)
                    VALUES (?, ?, 1)
                    ON CONFLICT(guild_id, inviter_id) DO UPDATE SET joins = joins + 1
                """, (str(guild.id), str(inviter.id)))
                await db.commit()
            
            # Find a welcome channel
            channel = discord.utils.get(guild.text_channels, name="welcome") or guild.text_channels[0]
            await channel.send(f"📥 **{member.name}** joined! Invited by **{inviter.name}**.")

    @commands.command(name="invites")
    async def show_invites(self, ctx, user: discord.Member = None):
        """📈 Check how many people you (or someone else) have invited."""
        target = user or ctx.author
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT joins FROM invite_stats WHERE guild_id = ? AND inviter_id = ?",
                (str(ctx.guild.id), str(target.id))
            ) as cursor:
                row = await cursor.fetchone()
        
        count = row[0] if row else 0
        await ctx.send(f"📊 **{target.display_name}** has invited **{count}** members to the server.")

async def setup(bot):
    await bot.add_cog(Invites(bot))
