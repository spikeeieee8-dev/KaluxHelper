import discord
from discord.ext import commands
import aiosqlite
import datetime
from main.config import DB_PATH, COLOR_ERROR, COLOR_SUCCESS, COLOR_WARN

class Guard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guard_settings (
                    guild_id TEXT PRIMARY KEY,
                    quarantine_role_id TEXT,
                    log_channel_id TEXT,
                    whitelist TEXT DEFAULT ''
                )""")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS quarantined_users (
                    user_id TEXT,
                    guild_id TEXT,
                    old_roles TEXT,
                    PRIMARY KEY (user_id, guild_id)
                )""")
            await db.commit()

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    async def is_whitelisted(self, guild_id, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT whitelist FROM guard_settings WHERE guild_id = ?", (str(guild_id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    whitelist = row[0].split(",")
                    return str(user_id) in whitelist or str(user_id) == str(self.bot.owner_id)
        return str(user_id) == str(self.bot.owner_id)

    async def get_guard_log(self, guild):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT log_channel_id FROM guard_settings WHERE guild_id = ?", (str(guild.id),)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return guild.get_channel(int(row[0]))
        return None

    async def punish_user(self, member, reason):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT quarantine_role_id FROM guard_settings WHERE guild_id = ?", (str(member.guild.id),)) as cursor:
                row = await cursor.fetchone()
                if not row or not row[0]: return
                q_role = member.guild.get_role(int(row[0]))
        
        if not q_role: return

        role_ids = [str(r.id) for r in member.roles if not r.is_default()]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO quarantined_users VALUES (?, ?, ?)", 
                             (str(member.id), str(member.guild.id), ",".join(role_ids)))
            await db.commit()

        try:
            await member.edit(roles=[q_role], reason=f"Guard: {reason}")
        except:
            pass

        log_channel = await self.get_guard_log(member.guild)
        if log_channel:
            embed = discord.Embed(
                title="🚨 SECURITY ALERT",
                description=f"**User:** {member.mention}\n**Action:** {reason}\n**Status:** Quarantined.",
                color=COLOR_ERROR,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await log_channel.send(embed=embed)

    # ─── Quarantine Commands ──────────────────────────────────────────────────

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def quarantine(self, ctx):
        """🔒 Quarantine System: !quarantine add @user | !quarantine remove @user"""
        await ctx.send("Usage: `!quarantine add @user` or `!quarantine remove @user`")

    @quarantine.command(name="add")
    @commands.has_permissions(administrator=True)
    async def q_add(self, ctx, member: discord.Member):
        if await self.is_whitelisted(ctx.guild.id, member.id):
            return await ctx.send("❌ Cannot quarantine a whitelisted user.")
        await self.punish_user(member, f"Manually quarantined by {ctx.author}")
        await ctx.send(f"🔒 {member.mention} has been quarantined.")

    @quarantine.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def q_remove(self, ctx, member: discord.Member):
        await self.unquarantine(ctx, member)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unquarantine(self, ctx, member: discord.Member):
        """🔓 Restore a user's roles."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT old_roles FROM quarantined_users WHERE user_id = ? AND guild_id = ?", (str(member.id), str(ctx.guild.id))) as cursor:
                row = await cursor.fetchone()
        
        if not row: return await ctx.send("❌ User not found in quarantine records.")

        role_ids = row[0].split(",")
        roles = [ctx.guild.get_role(int(rid)) for rid in role_ids if ctx.guild.get_role(int(rid))]
        
        try:
            await member.edit(roles=roles, reason="Manual Release")
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("DELETE FROM quarantined_users WHERE user_id = ? AND guild_id = ?", (str(member.id), str(ctx.guild.id)))
                await db.commit()
            await ctx.send(f"✅ {member.mention} restored.")
        except:
            await ctx.send("❌ Error restoring roles. Check hierarchy.")

    # ─── Guard Setup Commands ─────────────────────────────────────────────────

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def guard(self, ctx):
        await ctx.send("Usage: `!guard setlogs #chan`, `!guard setrole @role`, `!guard whitelist @user`")

    @guard.command()
    async def setlogs(self, ctx, channel: discord.TextChannel):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO guard_settings (guild_id, log_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET log_channel_id = ?", (str(ctx.guild.id), str(channel.id), str(channel.id)))
            await db.commit()
        await ctx.send(f"✅ Guard logs set to {channel.mention}")

    @guard.command()
    async def setrole(self, ctx, role: discord.Role):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO guard_settings (guild_id, quarantine_role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET quarantine_role_id = ?", (str(ctx.guild.id), str(role.id), str(role.id)))
            await db.commit()
        await ctx.send(f"✅ Quarantine role set to {role.mention}")

    @guard.command()
    async def whitelist(self, ctx, user: discord.User):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT whitelist FROM guard_settings WHERE guild_id = ?", (str(ctx.guild.id),)) as cursor:
                row = await cursor.fetchone()
                current = row[0] if row else ""
            new_wl = f"{current},{user.id}".strip(",")
            await db.execute("INSERT INTO guard_settings (guild_id, whitelist) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET whitelist = ?", (str(ctx.guild.id), new_wl, new_wl))
            await db.commit()
        await ctx.send(f"🛡️ {user.mention} whitelisted.")

    # ─── Security Listeners ───────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
            if await self.is_whitelisted(channel.guild.id, entry.user.id): return
            await self.punish_user(entry.user, f"Deleted channel: #{channel.name}")
            await channel.clone(reason="Guard Revert")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
            if await self.is_whitelisted(role.guild.id, entry.user.id): return
            await self.punish_user(entry.user, f"Deleted role: @{role.name}")
            await role.guild.create_role(name=role.name, permissions=role.permissions, color=role.color, reason="Guard Revert")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
            if entry.target.id == member.id:
                if await self.is_whitelisted(member.guild.id, entry.user.id): return
                await self.punish_user(entry.user, f"Kicked: {member.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.target.id == user.id:
                if await self.is_whitelisted(guild.id, entry.user.id): return
                await self.punish_user(entry.user, f"Banned: {user.name}")
                await guild.unban(user, reason="Guard Revert")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot: return
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
            if await self.is_whitelisted(member.guild.id, entry.user.id): return
            await self.punish_user(entry.user, f"Added unauthorized bot: {member.name}")
            await member.kick(reason="Guard: Unauthorized Bot")

async def setup(bot):
    await bot.add_cog(Guard(bot))
