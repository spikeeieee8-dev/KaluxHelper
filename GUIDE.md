# KaluxHost Discord Bot — Full Guide

A comprehensive reference for the bot's architecture, all commands, how to extend it safely, and how to deploy it on a VPS.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [How Everything Works](#2-how-everything-works)
3. [All Commands Reference](#3-all-commands-reference)
4. [How to Add a New Module (Without Breaking Anything)](#4-how-to-add-a-new-module-without-breaking-anything)
5. [Database Schema](#5-database-schema)
6. [Deploying on a VPS](#6-deploying-on-a-vps)
7. [Environment Variables & Secrets](#7-environment-variables--secrets)
8. [Common Troubleshooting](#8-common-troubleshooting)

---

## 1. Project Structure

```
artifacts/discord-bot/
├── bot.py                  ← Entry point (run this file)
├── requirements.txt        ← Python dependencies
├── GUIDE.md                ← This file
│
├── main/
│   ├── bot.py              ← KaluxBot class: intents, cog loader, error handler
│   ├── config.py           ← All constants: token, colours, paths
│   └── utils/
│       ├── database.py     ← SQLite helpers for warnings, prefixes, module states
│       └── embeds.py       ← Brand-consistent embed builders (success/error/warn/brand)
│
├── modules/                ← Every .py file here is auto-loaded as a cog at startup
│   ├── admin.py            ← Prefix, say, announce
│   ├── hosting.py          ← Plans, status, uptime, node info
│   ├── info.py             ← Help, ping, serverinfo, userinfo, botinfo
│   ├── moderation.py       ← Ban, kick, mute, warn, purge, lock, slowmode
│   ├── panel.py            ← Setup panel (sendticketpanel, etc.)
│   └── tickets.py          ← Full ticket system (claim, close, rate, stats, leaderboard)
│
└── data/                   ← Created automatically at runtime
    ├── kaluxhost.db        ← SQLite database
    └── transcripts/        ← Saved ticket transcripts (.txt files)
```

**Golden rule:** All files that need to persist data use `data/kaluxhost.db`. Transcripts go to `data/transcripts/`. Both are created automatically — you never need to create them manually.

---

## 2. How Everything Works

### Bot Startup

1. `bot.py` (entry point) imports `KaluxBot` from `main/bot.py` and calls `asyncio.run(KaluxBot().start_bot())`.
2. `setup_hook()` runs before the bot connects to Discord:
   - Calls `init_db()` to create all core tables (guild_settings, warnings, module_states).
   - Calls `_load_all_modules()` which scans the `modules/` directory and loads every `.py` file as a Discord cog extension.
3. Each module's `setup()` function is called automatically when the module loads. The tickets module also calls `_init_db()` to create ticket-specific tables and registers persistent Views.
4. `on_ready()` fires once connected — sets presence and prints startup info to console.

### Dynamic Prefix

Every command checks the prefix from the database (`guild_settings.prefix`). Default is `!`. If a guild changes the prefix via `!setprefix`, that value is stored in SQLite and used for all future commands in that guild.

### Cog System (Modules)

Each file in `modules/` is a Discord "cog" — a class that groups related commands and listeners. The bot auto-discovers and loads all of them. Cogs can have:
- **Prefix commands** (`@commands.command`) — e.g. `!ban`
- **Slash commands** (`@app_commands.command`) — e.g. `/ban`
- **Listeners** (`@commands.Cog.listener()`) — e.g. `on_message`

### Global Error Handler

`main/bot.py` has `on_command_error()` which catches common errors (missing perms, wrong args, cooldown) and shows clean embed messages. Unhandled errors are printed to stderr and show a generic "An unexpected error occurred" message.

### Ticket Lifecycle

```
User opens ticket
  → Panel buttons (General / Billing / Report)
  → Channel created with restricted permissions
  → Staff can READ but NOT write (until they claim)
  → Staff presses Claim button
  → Claimer gets write permission
  → on_message warns other staff/admins who try to write without claiming
  → Staff presses Close Ticket (or user does)
  → If staff closed: reason modal appears
  → Rating view (1-5 ⭐) shown to user
  → After rating: StaffActionView (Delete / Reopen)
  → Delete: transcript saved → log embed sent → channel deleted
  → Reopen: ticket resets, claim cleared, flow restarts
```

### Staff Stats

Every time a rated ticket is closed, the claiming staff member's stats are updated:
- `tickets_handled += 1`
- `total_rating += stars`
- `rating_count += 1`

These feed into `!staffstats` and `!leaderboard`.

### Duty Tracking (`!on` / `!off`)

- `!on` sets `on_duty_since = now` in `staff_stats`.
- `!off` calculates `session_secs = now - on_duty_since`, adds to `total_duty_secs`, and clears `on_duty_since`.
- **Abuse prevention (layered):**
  1. Command-level cooldown: 30 seconds between each use (Discord-enforced).
  2. Cannot go `!on` again within 5 minutes of going `!off` (stored in `last_off_duty`).
  3. Must be on duty for at least 5 minutes before running `!off`.

---

## 3. All Commands Reference

### Prefix: `!` (configurable per server)

#### Admin
| Command | Permission | Description |
|---|---|---|
| `!setprefix <prefix>` | Manage Guild | Change the bot prefix for this server |
| `!prefix` | Everyone | Show the current prefix |
| `!say <message>` | Manage Messages | Make the bot send a plain message |
| `!announce <#channel> <message>` | Manage Guild | Send a branded announcement embed |

#### Moderation
| Command | Permission | Description |
|---|---|---|
| `!ban <member> [reason]` | Ban Members | Ban a member |
| `!kick <member> [reason]` | Kick Members | Kick a member |
| `!mute <member> [minutes] [reason]` | Moderate Members | Timeout a member |
| `!unmute <member>` | Moderate Members | Remove timeout |
| `!warn <member> [reason]` | Moderate Members | Add a warning |
| `!warnings [member]` | Everyone | View warnings for a member |
| `!clearwarns <member>` | Moderate Members | Clear all warnings |
| `!purge [amount]` | Manage Messages | Bulk delete messages (max 100) |
| `!slowmode [seconds]` | Manage Channels | Set channel slowmode |
| `!lock [#channel]` | Manage Channels | Lock a channel |
| `!unlock [#channel]` | Manage Channels | Unlock a channel |

#### Info
| Command | Permission | Description |
|---|---|---|
| `!help [module]` | Everyone | Show all commands or module commands |
| `!ping` | Everyone | Check bot latency |
| `!serverinfo` | Everyone | Server info embed |
| `!userinfo [member]` | Everyone | User info embed |
| `!botinfo` | Everyone | Bot version and stats |

#### Hosting
| Command | Permission | Description |
|---|---|---|
| `!plans` | Everyone | Show hosting plans |
| `!status` | Everyone | Show service status |
| `!uptime` | Everyone | Bot uptime and latency |
| `!support` | Everyone | Support contact info |
| `!node` | Everyone | Network node locations |

#### Tickets
| Command | Permission | Description |
|---|---|---|
| `!setstaffrole <@role>` | Administrator | Set the staff role |
| `!setlogchannel [#channel]` | Administrator | Set the ticket log channel |
| `!ticket` | Everyone | Open a ticket (shows category selector) |
| `!on` | Staff | Go on duty (30s cooldown, 5min cooldown after going off) |
| `!off` | Staff | Go off duty (must be on for 5min minimum, 30s cooldown) |
| `!unclaim` | Claimer only | Unclaim the current ticket |
| `!rep <@member>` | Everyone | Give a rep to a staff member (once per 24h) |
| `!staffstats [member]` | Everyone | View staff stats |
| `!leaderboard` | Everyone | Top 10 staff leaderboard |

#### Slash Commands
All major commands also have slash variants: `/ban`, `/kick`, `/mute`, `/warn`, `/purge`, `/ping`, `/serverinfo`, `/userinfo`, `/setprefix`, `/prefix`, `/plans`, `/status`, `/uptime`, `/ticket`, `/staffstats`, `/leaderboard`, `/rep`

---

## 4. How to Add a New Module (Without Breaking Anything)

### Step 1 — Create your module file

Create `modules/your_module.py`. Follow this template:

```python
"""
YOUR MODULE NAME
Brief description of what it does.
"""
import discord
from discord import app_commands
from discord.ext import commands

from main.config import COLOR_BRAND
from main.utils.embeds import success, error, warn, brand


class YourModule(commands.Cog, name="YourModule"):
    """📦 Short description shown in !help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="yourcommand")
    @commands.guild_only()
    async def your_cmd(self, ctx: commands.Context):
        """Brief command description for !help."""
        await ctx.reply(embed=success("It works!"), mention_author=False)

    # Slash variant (optional but recommended)
    @app_commands.command(name="yourcommand", description="What this command does")
    @app_commands.guild_only()
    async def slash_your_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=success("It works!"))


async def setup(bot: commands.Bot):
    await bot.add_cog(YourModule(bot))
```

### Step 2 — Add a database table (if your module needs data)

Add your table creation SQL inside `setup()` before adding the cog:

```python
import aiosqlite
from main.config import DB_PATH

async def setup(bot: commands.Bot):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS your_table (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                data     TEXT NOT NULL
            );
        """)
        await db.commit()
    await bot.add_cog(YourModule(bot))
```

**Important:** Always use `CREATE TABLE IF NOT EXISTS` — this is safe to run on every startup and won't overwrite existing data.

### Step 3 — Nothing else needed

The bot auto-discovers every `.py` file in `modules/` at startup. Your new module will be loaded automatically. No registration or import changes needed.

### Rules for safe additions

- **Never rename or remove existing tables or columns** — other modules depend on them.
- **Use additive-only migrations** — if you need a new column on an existing table, use:
  ```python
  try:
      await db.execute("ALTER TABLE existing_table ADD COLUMN new_col TEXT")
      await db.commit()
  except Exception:
      pass  # Column already exists — safe to ignore
  ```
- **Don't change `main/config.py` constants** other than adding new ones — every module imports from it.
- **Don't override `on_command_error`** in your cog — the global handler in `main/bot.py` already covers it. Only handle errors specific to your cog if needed.
- **Test in a development server first** before using in production.

---

## 5. Database Schema

The bot uses a single SQLite file: `data/kaluxhost.db`.

### `guild_settings`
| Column | Type | Description |
|---|---|---|
| guild_id | TEXT PK | Discord guild ID |
| prefix | TEXT | Per-server command prefix (default `!`) |

### `warnings`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-incrementing ID |
| guild_id | TEXT | Guild ID |
| user_id | TEXT | Warned user ID |
| mod_id | TEXT | Moderator who warned |
| reason | TEXT | Warning reason |
| created_at | INTEGER | Unix timestamp |

### `module_states`
| Column | Type | Description |
|---|---|---|
| module_name | TEXT PK | Module name |
| enabled | INTEGER | 1 = enabled, 0 = disabled |

### `ticket_config`
| Column | Type | Description |
|---|---|---|
| guild_id | TEXT PK | Guild ID |
| staff_role_id | TEXT | Staff role ID |
| log_channel_id | TEXT | Log channel ID |
| ticket_counter | INTEGER | Auto-incrementing ticket number |

### `tickets`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Internal ticket ID |
| guild_id | TEXT | Guild ID |
| channel_id | TEXT UNIQUE | Discord channel ID |
| user_id | TEXT | Ticket opener's user ID |
| category | TEXT | `general`, `billing`, or `report` |
| status | TEXT | `open` or `closed` |
| claimed_by | TEXT | Staff user ID who claimed (NULL if unclaimed) |
| open_time | INTEGER | Unix timestamp when opened |
| close_time | INTEGER | Unix timestamp when closed |
| close_reason | TEXT | Reason provided on close |
| rating | INTEGER | User rating 1-5 (NULL if not rated) |
| ticket_number | INTEGER | Human-readable ticket number |

### `staff_stats`
| Column | Type | Description |
|---|---|---|
| guild_id | TEXT | Guild ID |
| user_id | TEXT | Staff user ID |
| tickets_handled | INTEGER | Total tickets closed with a rating |
| total_rating | INTEGER | Sum of all star ratings received |
| rating_count | INTEGER | Number of ratings received |
| rep_count | INTEGER | Total reps received |
| total_duty_secs | INTEGER | Cumulative on-duty seconds |
| on_duty_since | INTEGER | Unix timestamp of current duty start (NULL if off) |
| last_off_duty | INTEGER | Unix timestamp of last time they went off duty |

### `reps`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-incrementing ID |
| guild_id | TEXT | Guild ID |
| from_user_id | TEXT | Who gave the rep |
| to_user_id | TEXT | Who received the rep |
| created_at | INTEGER | Unix timestamp (used for 24h cooldown check) |

---

## 6. Deploying on a VPS

### Requirements

- Ubuntu 22.04 / 24.04 (or any Debian-based Linux)
- Python 3.12+
- Git

### Step 1 — Connect to your VPS

```bash
ssh root@your.server.ip
```

### Step 2 — Install Python and system dependencies

```bash
apt update && apt upgrade -y
apt install -y python3.12 python3.12-venv python3-pip git
```

### Step 3 — Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git /opt/kaluxhost-bot
cd /opt/kaluxhost-bot/artifacts/discord-bot
```

Or, if uploading files manually via SFTP, put them in `/opt/kaluxhost-bot/artifacts/discord-bot/`.

### Step 4 — Set up a Python virtual environment

```bash
cd /opt/kaluxhost-bot/artifacts/discord-bot
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### Step 5 — Set the Discord bot token

Create a `.env` file (or use environment variables directly):

```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
```

Or store it permanently in `/etc/environment`:

```
DISCORD_BOT_TOKEN=your_bot_token_here
```

Then reload: `source /etc/environment`

### Step 6 — Test that the bot starts

```bash
cd /opt/kaluxhost-bot/artifacts/discord-bot
DISCORD_BOT_TOKEN=your_token_here .venv/bin/python bot.py
```

You should see the startup banner and "✅ Online as ..." in the console. Press `Ctrl+C` to stop.

### Step 7 — Run the bot as a background service (systemd)

Create a service file so the bot auto-starts and restarts on crash:

```bash
nano /etc/systemd/system/kaluxhost-bot.service
```

Paste the following (replace `your_token_here`):

```ini
[Unit]
Description=KaluxHost Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kaluxhost-bot/artifacts/discord-bot
ExecStart=/opt/kaluxhost-bot/artifacts/discord-bot/.venv/bin/python bot.py
Restart=always
RestartSec=5
Environment=DISCORD_BOT_TOKEN=your_token_here

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable kaluxhost-bot
systemctl start kaluxhost-bot
```

### Step 8 — View logs

```bash
# Live logs
journalctl -u kaluxhost-bot -f

# Last 100 lines
journalctl -u kaluxhost-bot -n 100
```

### Updating the bot on your VPS

```bash
cd /opt/kaluxhost-bot
git pull
cd artifacts/discord-bot
.venv/bin/pip install -r requirements.txt   # only needed if requirements changed
systemctl restart kaluxhost-bot
journalctl -u kaluxhost-bot -f              # verify it started cleanly
```

### Keeping data safe

The database is at `artifacts/discord-bot/data/kaluxhost.db`. Back it up regularly:

```bash
# Manual backup
cp /opt/kaluxhost-bot/artifacts/discord-bot/data/kaluxhost.db \
   /opt/backups/kaluxhost-$(date +%Y%m%d).db

# Automated daily backup via cron
crontab -e
# Add this line:
0 3 * * * cp /opt/kaluxhost-bot/artifacts/discord-bot/data/kaluxhost.db /opt/backups/kaluxhost-$(date +\%Y\%m\%d).db
```

---

## 7. Environment Variables & Secrets

| Variable | Required | Description |
|---|---|---|
| `DISCORD_BOT_TOKEN` | ✅ Yes | Your bot's token from the Discord Developer Portal |

All other configuration (prefix, staff role, log channel) is stored per-guild in the database and managed via bot commands.

### Getting a Discord Bot Token

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Create a new application → Bot tab → Reset Token → copy the token
3. Enable **Message Content Intent**, **Server Members Intent**, and **Presence Intent** under Privileged Gateway Intents
4. Invite the bot with the OAuth2 URL Generator: select `bot` + `applications.commands` scopes, then select the permissions you need (at minimum: View Channels, Send Messages, Manage Channels, Manage Messages, Embed Links, Attach Files, Read Message History, Add Reactions, Moderate Members, Ban Members, Kick Members)

---

## 8. Common Troubleshooting

### Bot won't start — "DISCORD_BOT_TOKEN is not set"
Set the environment variable before running the bot:
```bash
export DISCORD_BOT_TOKEN="your_token"
```

### "An unexpected error occurred" on a command
Check the console output (`journalctl -u kaluxhost-bot -n 50` on VPS, or the Replit console). The actual error is printed there. Common causes:
- Missing database column (run the bot — it auto-migrates on startup)
- Discord permission issue (bot needs correct role permissions)

### Leaderboard shows no entries
Staff stats are only populated when a ticket is rated by the user. Have at least one ticket go through the full flow (open → claim → close → rate).

### Slash commands not showing up
Slash commands sync globally when the bot starts. This can take up to 1 hour to propagate across Discord. To force-sync to a specific guild during development, add `await self.bot.tree.sync(guild=discord.Object(id=YOUR_GUILD_ID))` in `on_ready`.

### Bot keeps restarting on VPS
Check `journalctl -u kaluxhost-bot -n 50` for the error. Most common: bad token, missing Python packages, or a syntax error in a module. Fix the issue and run `systemctl start kaluxhost-bot`.

### Ticket channels aren't created in the right category
Update the `CATEGORY_MAP` in `modules/tickets.py` with your server's actual Discord category IDs. Right-click a category → Copy ID (enable Developer Mode in Discord settings first).

### Staff can still message without claiming (admins)
This is by design — Discord administrators bypass all channel permission overwrites. The bot now detects this and sends a 12-second reminder in the channel warning them to claim first.
