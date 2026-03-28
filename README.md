# KaluxHost Discord Bot

A fully modular, cog-based Discord bot built in Python for the KaluxHost server.

## Structure

```
discord-bot/
├── bot.py                  ← Entry point
├── requirements.txt
├── main/                   ← Core bot engine (don't touch for new features)
│   ├── bot.py              ← Bot class, cog loader, error handler
│   ├── config.py           ← All constants (colors, paths, token)
│   └── utils/
│       ├── database.py     ← Async SQLite helpers (prefix, warnings)
│       └── embeds.py       ← Branded embed builders
├── modules/                ← Drop new .py files here to add features
│   ├── panel.py            ← Module manager (load/unload/reload live)
│   ├── info.py             ← help, ping, serverinfo, userinfo, botinfo
│   ├── moderation.py       ← ban, kick, mute, warn, purge, lock, etc.
│   ├── admin.py            ← setprefix, prefix, say, announce
│   └── hosting.py          ← plans, status, uptime, support, ticket, node
└── data/
    └── kaluxhost.db        ← SQLite database (auto-created)
```

## Commands

### Panel (Module Manager)
| Command | Description |
|---------|-------------|
| `!modules` | List all modules and their status |
| `!load <name>` | Load a module |
| `!unload <name>` | Unload a module |
| `!reload <name>` | Hot-reload a module (picks up code changes) |
| `!reloadall` | Reload all loaded modules |

### Info
`!help` `!ping` `!serverinfo` `!userinfo` `!botinfo`

### Moderation
`!ban` `!kick` `!mute` `!unmute` `!warn` `!warnings` `!clearwarns` `!purge` `!slowmode` `!lock` `!unlock`

### Admin
`!setprefix` `!prefix` `!say` `!announce`

### Hosting
`!plans` `!status` `!uptime` `!support` `!ticket` `!node`

All commands also have `/slash` equivalents.

## Adding a New Module

1. Create `modules/my-module.py`
2. Write a `Cog` class and an `async def setup(bot)` function
3. The bot auto-loads it on restart — or use `!load my-module` to load it live

```python
# modules/my-module.py
from discord.ext import commands
from main.utils.embeds import brand

class MyModule(commands.Cog, name="MyModule"):
    """🎯 My new module."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mycommand")
    async def my_cmd(self, ctx):
        await ctx.reply(embed=brand("Hello!", "This is my new command."))

async def setup(bot):
    await bot.add_cog(MyModule(bot))
```

Then run `!load my-module` — no restart needed.

## Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `DISCORD_BOT_TOKEN` | ✅ | Bot token from Discord Developer Portal |

## Required Bot Permissions & Intents

Enable in the Discord Developer Portal under **Bot → Privileged Gateway Intents**:
- ✅ Server Members Intent
- ✅ Message Content Intent

Bot permissions: `Send Messages`, `Read Message History`, `Manage Messages`, `Kick Members`, `Ban Members`, `Moderate Members`, `Manage Channels`
