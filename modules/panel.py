"""
PANEL MODULE
Lets admins load, unload, reload, and list modules (cogs) without restarting.
Owner-only by default — the most powerful module in the bot.

Commands (prefix only — these are bot management tools):
  !modules          — list all modules and their status
  !load   <name>    — load a module
  !unload <name>    — unload a module
  !reload <name>    — reload a module (hot-reload code changes)
  !reloadall        — reload every loaded module at once
"""
import os
import sys
import discord
from discord.ext import commands

from main.config import MODULES_DIR
from main.utils.embeds import brand, success, error, warn


class Panel(commands.Cog, name="Panel"):
    """🎛️ Module manager — load/unload/reload cogs live."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Guard: bot owner or server admin ─────────────────────────────────────

    async def cog_check(self, ctx: commands.Context) -> bool:
        is_owner = await self.bot.is_owner(ctx.author)
        is_admin = ctx.guild and ctx.author.guild_permissions.administrator
        if not (is_owner or is_admin):
            await ctx.reply(embed=error("Only bot owners or server admins can use the panel."), mention_author=False)
            return False
        return True

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _all_module_files(self) -> list[str]:
        """Return sorted list of module names (filename without .py)."""
        return sorted(
            f[:-3]
            for f in os.listdir(MODULES_DIR)
            if f.endswith(".py") and not f.startswith("_")
        )

    def _loaded_modules(self) -> list[str]:
        return [
            ext.split(".")[-1]
            for ext in self.bot.extensions
            if ext.startswith("modules.")
        ]

    # ── Commands ──────────────────────────────────────────────────────────────

    @commands.command(name="modules", aliases=["cogs", "mods"])
    async def list_modules(self, ctx: commands.Context):
        """List every module and whether it's loaded."""
        all_mods   = self._all_module_files()
        loaded     = set(self._loaded_modules())

        lines = []
        for mod in all_mods:
            status = "🟢 Loaded" if mod in loaded else "🔴 Unloaded"
            lines.append(f"`{mod:<18}` {status}")

        embed = brand(
            "🎛️ Module Panel",
            "\n".join(lines) if lines else "No modules found in /modules/"
        )
        embed.set_footer(text=f"KaluxHost Bot | {len(loaded)}/{len(all_mods)} modules loaded")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="load")
    async def load_module(self, ctx: commands.Context, name: str):
        """Load a module by name."""
        ext = f"modules.{name.lower()}"
        try:
            await self.bot.load_extension(ext)
            await ctx.reply(embed=success(f"Loaded module `{name}`."), mention_author=False)
            print(f"[PANEL] Loaded: {name} by {ctx.author}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.reply(embed=warn(f"`{name}` is already loaded. Use `!reload {name}` to refresh it."), mention_author=False)
        except commands.ExtensionNotFound:
            await ctx.reply(embed=error(f"Module `{name}` not found in `/modules/`."), mention_author=False)
        except Exception as exc:
            await ctx.reply(embed=error(f"Failed to load `{name}`:\n```{exc}```"), mention_author=False)

    @commands.command(name="unload")
    async def unload_module(self, ctx: commands.Context, name: str):
        """Unload a module by name (panel itself cannot be unloaded)."""
        if name.lower() == "panel":
            return await ctx.reply(embed=error("Cannot unload the Panel module."), mention_author=False)
        ext = f"modules.{name.lower()}"
        try:
            await self.bot.unload_extension(ext)
            await ctx.reply(embed=success(f"Unloaded module `{name}`."), mention_author=False)
            print(f"[PANEL] Unloaded: {name} by {ctx.author}")
        except commands.ExtensionNotLoaded:
            await ctx.reply(embed=warn(f"`{name}` isn't loaded."), mention_author=False)
        except Exception as exc:
            await ctx.reply(embed=error(f"Failed to unload `{name}`:\n```{exc}```"), mention_author=False)

    @commands.command(name="reload")
    async def reload_module(self, ctx: commands.Context, name: str):
        """Reload a module — picks up code changes without restarting."""
        ext = f"modules.{name.lower()}"
        try:
            await self.bot.reload_extension(ext)
            await ctx.reply(embed=success(f"Reloaded module `{name}`."), mention_author=False)
            print(f"[PANEL] Reloaded: {name} by {ctx.author}")
        except commands.ExtensionNotLoaded:
            # Try loading it fresh
            try:
                await self.bot.load_extension(ext)
                await ctx.reply(embed=success(f"Loaded (was unloaded) module `{name}`."), mention_author=False)
            except Exception as exc:
                await ctx.reply(embed=error(f"Failed:\n```{exc}```"), mention_author=False)
        except Exception as exc:
            await ctx.reply(embed=error(f"Failed to reload `{name}`:\n```{exc}```"), mention_author=False)

    @commands.command(name="reloadall", aliases=["reloadmodules"])
    async def reload_all(self, ctx: commands.Context):
        """Reload every loaded module at once."""
        loaded   = list(self._loaded_modules())
        ok, fail = [], []

        for name in loaded:
            ext = f"modules.{name}"
            try:
                await self.bot.reload_extension(ext)
                ok.append(name)
            except Exception as exc:
                fail.append(f"{name} ({exc})")

        desc = f"✅ Reloaded: {', '.join(f'`{n}`' for n in ok)}" if ok else ""
        if fail:
            desc += f"\n❌ Failed: {', '.join(f'`{n}`' for n in fail)}"

        await ctx.reply(embed=brand("🔄 Reload All", desc or "Nothing to reload."), mention_author=False)
        print(f"[PANEL] ReloadAll by {ctx.author}: ok={ok} fail={fail}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Panel(bot))
