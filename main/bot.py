"""
KaluxHost Bot — Core
Handles cog auto-loading, dynamic prefix, and startup.
"""
import os
import sys
import datetime
import discord
from discord.ext import commands

from main.config import DEFAULT_PREFIX, TOKEN, BOT_NAME, BOT_VERSION, MODULES_DIR
from main.utils.database import init_db, get_prefix


# ── Dynamic prefix resolver ───────────────────────────────────────────────────

async def get_command_prefix(bot: commands.Bot, message: discord.Message):
    if not message.guild:
        return DEFAULT_PREFIX
    return await get_prefix(message.guild.id)


# ── Bot class ─────────────────────────────────────────────────────────────────

class KaluxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members          = True
        intents.moderation       = True

        super().__init__(
            command_prefix=get_command_prefix,
            intents=intents,
            help_command=None,              # We have our own !help
            case_insensitive=True,
            strip_after_prefix=True,
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def setup_hook(self):
        """Called before the bot connects. Load DB + all modules."""
        await init_db()
        await self._load_all_modules()

    async def _load_all_modules(self):
        """Auto-load every .py file inside /modules/ (except __init__.py)."""
        loaded, failed = [], []
        for filename in sorted(os.listdir(MODULES_DIR)):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue
            module_name = filename[:-3]
            ext = f"modules.{module_name}"
            try:
                await self.load_extension(ext)
                loaded.append(module_name)
            except Exception as exc:
                failed.append((module_name, exc))
                print(f"  [MODULE ERROR] {module_name}: {exc}", file=sys.stderr)

        print(f"\n{'─'*50}")
        print(f"  {BOT_NAME} Bot v{BOT_VERSION}")
        print(f"  Modules loaded : {', '.join(loaded) or 'none'}")
        if failed:
            print(f"  Modules failed : {', '.join(n for n, _ in failed)}")
        print(f"{'─'*50}\n")

    async def on_ready(self):
        self.start_time = getattr(self, "start_time", datetime.datetime.now(datetime.timezone.utc))
        print(f"✅  Online as {self.user} (ID: {self.user.id})")
        print(f"📡  Connected to {len(self.guilds)} guild(s)\n")
        await self.change_presence(
            activity=discord.CustomActivity(name=f"KaluxHost | !help")
        )

    async def on_command_error(self, ctx: commands.Context, error):
        """Global error handler — catches common errors cleanly."""
        from main.utils.embeds import error as err_embed

        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            return await ctx.reply(embed=err_embed(f"You need: **{perms}**"), mention_author=False)
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            return await ctx.reply(embed=err_embed(f"I need: **{perms}**"), mention_author=False)
        if isinstance(error, commands.MemberNotFound):
            return await ctx.reply(embed=err_embed("Member not found."), mention_author=False)
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.reply(embed=err_embed(f"Missing argument: `{error.param.name}`"), mention_author=False)
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.reply(embed=err_embed(f"Slow down! Try again in **{error.retry_after:.1f}s**"), mention_author=False)
        if isinstance(error, commands.CheckFailure):
            return await ctx.reply(embed=err_embed("You don't have permission to use that."), mention_author=False)

        # Unexpected — print to console for debugging
        print(f"[UNHANDLED ERROR] {ctx.command}: {error}", file=sys.stderr)
        await ctx.reply(embed=err_embed("An unexpected error occurred."), mention_author=False)

    async def start_bot(self):
        async with self:
            await self.start(TOKEN)
