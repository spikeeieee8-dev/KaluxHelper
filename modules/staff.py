"""
STAFF MODULE
Commands: addstaff, removestaff, stafflist, staffcheck
Bot staff management — allows non-admin Discord users to use admin commands.
"""
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, error, brand, warn


# ─── DB Helpers ──────────────────────────────────────────────────────────────

async def _init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_staff (
                guild_id TEXT NOT NULL,
                user_id  TEXT NOT NULL,
                role     TEXT NOT NULL DEFAULT 'staff',
                added_by TEXT,
                added_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        await db.commit()


async def is_bot_staff(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM bot_staff WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        ) as cur:
            return await cur.fetchone() is not None


async def get_bot_staff(guild_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bot_staff WHERE guild_id = ? ORDER BY added_at DESC",
            (str(guild_id),)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ─── Staff check decorator ────────────────────────────────────────────────────

def is_staff_or_admin():
    """Check: user is admin OR in bot_staff table."""
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        return await is_bot_staff(ctx.guild.id, ctx.author.id)
    return commands.check(predicate)


# ─── Cog ─────────────────────────────────────────────────────────────────────

class Staff(commands.Cog, name="Staff"):
    """⭐ Bot staff management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── !addstaff ─────────────────────────────────────────────────────────────

    @commands.command(name="addstaff", aliases=["staffadd"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def addstaff_cmd(self, ctx: commands.Context, member: discord.Member, role: str = "staff"):
        """Add a member to bot staff. Roles: staff, moderator, admin"""
        if role not in ("staff", "moderator", "admin"):
            return await ctx.reply(embed=error("Role must be: `staff`, `moderator`, or `admin`"), mention_author=False)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO bot_staff (guild_id, user_id, role, added_by) VALUES (?,?,?,?)",
                (str(ctx.guild.id), str(member.id), role, str(ctx.author.id))
            )
            await db.commit()

        await ctx.reply(
            embed=success(f"✅ Added {member.mention} to bot staff as **{role}**\nThey can now use admin commands."),
            mention_author=False
        )

    # ── !removestaff ──────────────────────────────────────────────────────────

    @commands.command(name="removestaff", aliases=["staffremove"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def removestaff_cmd(self, ctx: commands.Context, member: discord.Member):
        """Remove a member from bot staff."""
        async with aiosqlite.connect(DB_PATH) as db:
            result = await db.execute(
                "DELETE FROM bot_staff WHERE guild_id = ? AND user_id = ?",
                (str(ctx.guild.id), str(member.id))
            )
            await db.commit()

        if result.rowcount == 0:
            return await ctx.reply(embed=warn(f"{member.mention} is not in bot staff."), mention_author=False)

        await ctx.reply(
            embed=success(f"Removed {member.mention} from bot staff."),
            mention_author=False
        )

    # ── !stafflist ────────────────────────────────────────────────────────────

    @commands.command(name="stafflist", aliases=["staff", "listaff"])
    @commands.guild_only()
    async def stafflist_cmd(self, ctx: commands.Context):
        """List all bot staff members."""
        staff = await get_bot_staff(ctx.guild.id)

        if not staff:
            return await ctx.reply(
                embed=brand("⭐ Bot Staff", "No bot staff members yet.\nUse `!addstaff @user` to add someone."),
                mention_author=False
            )

        role_groups: dict[str, list[str]] = {"admin": [], "moderator": [], "staff": []}
        for s in staff:
            m = ctx.guild.get_member(int(s["user_id"]))
            name = m.mention if m else f"`{s['user_id']}`"
            role_groups.get(s["role"], role_groups["staff"]).append(name)

        embed = discord.Embed(title="⭐ KaluxHost Bot Staff", color=COLOR_BRAND)
        icons = {"admin": "👑", "moderator": "🛡️", "staff": "⭐"}
        for role_name, members in role_groups.items():
            if members:
                embed.add_field(
                    name=f"{icons[role_name]} {role_name.title()} ({len(members)})",
                    value="\n".join(members) or "None",
                    inline=False
                )
        embed.set_footer(text=f"Total: {len(staff)} staff members")
        await ctx.reply(embed=embed, mention_author=False)

    # ── !staffcheck ───────────────────────────────────────────────────────────

    @commands.command(name="staffcheck", aliases=["isstaff"])
    @commands.guild_only()
    async def staffcheck_cmd(self, ctx: commands.Context, member: discord.Member = None):
        """Check if a user is bot staff."""
        target = member or ctx.author
        staff_member = None

        if await is_bot_staff(ctx.guild.id, target.id):
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM bot_staff WHERE guild_id = ? AND user_id = ?",
                    (str(ctx.guild.id), str(target.id))
                ) as cur:
                    row = await cur.fetchone()
                    staff_member = dict(row) if row else None

        if staff_member:
            await ctx.reply(
                embed=success(f"✅ {target.mention} is bot staff — **{staff_member['role']}**"),
                mention_author=False
            )
        else:
            is_admin = target.guild_permissions.administrator
            if is_admin:
                await ctx.reply(embed=success(f"✅ {target.mention} is a server administrator."), mention_author=False)
            else:
                await ctx.reply(embed=error(f"{target.mention} is **not** bot staff."), mention_author=False)

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="addstaff", description="Add a member to bot staff")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def slash_addstaff(self, interaction: discord.Interaction, member: discord.Member,
                              role: str = "staff"):
        if role not in ("staff", "moderator", "admin"):
            return await interaction.response.send_message(embed=error("Role must be: staff, moderator, or admin"), ephemeral=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO bot_staff (guild_id, user_id, role, added_by) VALUES (?,?,?,?)",
                (str(interaction.guild.id), str(member.id), role, str(interaction.user.id))
            )
            await db.commit()
        await interaction.response.send_message(embed=success(f"Added {member.mention} as **{role}**"))

    @app_commands.command(name="removestaff", description="Remove a member from bot staff")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def slash_removestaff(self, interaction: discord.Interaction, member: discord.Member):
        async with aiosqlite.connect(DB_PATH) as db:
            result = await db.execute(
                "DELETE FROM bot_staff WHERE guild_id = ? AND user_id = ?",
                (str(interaction.guild.id), str(member.id))
            )
            await db.commit()
        if result.rowcount == 0:
            return await interaction.response.send_message(embed=warn(f"{member.mention} is not in bot staff."), ephemeral=True)
        await interaction.response.send_message(embed=success(f"Removed {member.mention} from bot staff."))

    @app_commands.command(name="stafflist", description="List all bot staff members")
    @app_commands.guild_only()
    async def slash_stafflist(self, interaction: discord.Interaction):
        staff = await get_bot_staff(interaction.guild.id)
        if not staff:
            return await interaction.response.send_message(embed=brand("⭐ Bot Staff", "No staff yet."))
        lines = [f"<@{s['user_id']}> — **{s['role']}**" for s in staff]
        embed = discord.Embed(title="⭐ Bot Staff", description="\n".join(lines), color=COLOR_BRAND)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await _init_db()
    await bot.add_cog(Staff(bot))
