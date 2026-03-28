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

This is a **full-stack platform** with three services that must all run on your VPS:

| Service | Language | What it does |
|---|---|---|
| **Discord Bot** | Python 3.12 | Connects to Discord, handles all commands and events |
| **API Server** | Node.js 20 | REST API used by the dashboard (port 3001) |
| **Dashboard** | React (static) | Served as pre-built HTML/JS/CSS via nginx |

nginx acts as the front door: it serves the dashboard files and proxies all `/api/*` requests to the Node.js API server. You only need one public port (80 / 443).

---

### Prerequisites

- **Ubuntu 22.04 or 24.04** (or any Debian-based Linux)
- A domain name or static IP pointed at the VPS *(optional, but required for HTTPS)*
- Root or sudo access

---

### Step 1 — Connect and update the server

```bash
ssh root@your.server.ip
apt update && apt upgrade -y
```

---

### Step 2 — Install system dependencies

```bash
# Python 3.12
apt install -y python3.12 python3.12-venv python3-pip

# Node.js 20 (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# pnpm (package manager for Node)
npm install -g pnpm

# nginx + git + extras
apt install -y nginx git curl
```

Verify versions:
```bash
python3.12 --version   # Python 3.12.x
node --version         # v20.x.x
pnpm --version         # 9.x or 10.x
nginx -v
```

---

### Step 3 — Upload the project files

**Option A — Git clone (recommended)**

```bash
git clone https://github.com/your-username/your-repo.git /opt/kaluxhost
```

**Option B — SFTP upload**

Upload the entire project folder to `/opt/kaluxhost` using FileZilla or any SFTP client. The structure should look like:

```
/opt/kaluxhost/
├── bot.py
├── requirements.txt
├── main/
├── modules/
├── data/
└── artifacts/
    ├── api-server/
    └── dashboard/
```

---

### Step 4 — Install Python dependencies

```bash
cd /opt/kaluxhost
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Test the install (expect an error about missing token — that's fine):
```bash
.venv/bin/python -c "import discord, aiosqlite, yt_dlp; print('OK')"
# Should print: OK
```

---

### Step 5 — Install Node.js dependencies

```bash
cd /opt/kaluxhost
pnpm install
```

This installs packages for both the API server and the dashboard in one command.

---

### Step 6 — Build the dashboard

The dashboard is a React app that needs to be compiled into static files once. nginx will serve these files directly — no Node.js process needed for the frontend.

```bash
cd /opt/kaluxhost/artifacts/dashboard
BASE_PATH=/ PORT=3000 pnpm build
```

The built files will be output to:
```
/opt/kaluxhost/artifacts/dashboard/dist/public/
```

You can verify the build succeeded:
```bash
ls /opt/kaluxhost/artifacts/dashboard/dist/public/
# Should show: index.html  assets/  ...
```

---

### Step 7 — Create the environment file

Create a shared secrets file that all three services will read from:

```bash
nano /opt/kaluxhost/.env
```

Paste and fill in your values:

```env
# Required — get from discord.com/developers/applications
DISCORD_BOT_TOKEN=your_bot_token_here

# Required — any long random string (used to sign login tokens for the dashboard)
# Generate one with: openssl rand -hex 48
JWT_SECRET=replace_with_a_long_random_string_here

# Optional — defaults to 3001 if not set
API_PORT=3001
```

Set strict permissions so only root can read it:

```bash
chmod 600 /opt/kaluxhost/.env
```

---

### Step 8 — Test each service manually

**Test the Discord bot** (should show startup banner then `✅ Online as ...`):
```bash
cd /opt/kaluxhost
set -a && source .env && set +a
.venv/bin/python bot.py
# Press Ctrl+C to stop once you see "Online as"
```

**Test the API server** (should print `KaluxHost API Server running on port 3001`):
```bash
cd /opt/kaluxhost/artifacts/api-server
set -a && source ../../.env && set +a
node --import tsx/esm src/index.ts
# Press Ctrl+C to stop
```

---

### Step 9 — Create systemd services

systemd keeps the services running and auto-restarts them if they crash.

**Service 1 — Discord Bot**

```bash
nano /etc/systemd/system/kaluxhost-bot.service
```

```ini
[Unit]
Description=KaluxHost Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kaluxhost
EnvironmentFile=/opt/kaluxhost/.env
ExecStart=/opt/kaluxhost/.venv/bin/python bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Service 2 — API Server**

```bash
nano /etc/systemd/system/kaluxhost-api.service
```

```ini
[Unit]
Description=KaluxHost API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kaluxhost/artifacts/api-server
EnvironmentFile=/opt/kaluxhost/.env
ExecStart=/usr/bin/node --import tsx/esm src/index.ts
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start both:

```bash
systemctl daemon-reload

systemctl enable kaluxhost-bot kaluxhost-api
systemctl start kaluxhost-bot kaluxhost-api

# Verify they're running
systemctl status kaluxhost-bot
systemctl status kaluxhost-api
```

---

### Step 10 — Configure nginx

nginx will:
- Serve the pre-built dashboard files for all normal requests
- Forward any request starting with `/api/` to the Node.js API server on port 3001

```bash
nano /etc/nginx/sites-available/kaluxhost
```

Paste the following (replace `your.domain.com` with your actual domain or server IP):

```nginx
server {
    listen 80;
    server_name your.domain.com;

    root /opt/kaluxhost/artifacts/dashboard/dist/public;
    index index.html;

    # Serve dashboard static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to the Node.js server
    location /api/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "";
        proxy_read_timeout 30s;
    }

    # Increase body size limit for API requests
    client_max_body_size 10M;
}
```

Enable the site and reload nginx:

```bash
# Enable the site
ln -s /etc/nginx/sites-available/kaluxhost /etc/nginx/sites-enabled/

# Remove the default nginx site (optional but avoids conflicts)
rm -f /etc/nginx/sites-enabled/default

# Test config is valid
nginx -t

# Reload nginx
systemctl reload nginx
systemctl enable nginx
```

Your dashboard should now be accessible at `http://your.domain.com`.

---

### Step 11 — Set up HTTPS with Let's Encrypt (optional but strongly recommended)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your.domain.com
```

Follow the prompts. Certbot will automatically edit your nginx config to add HTTPS and set up auto-renewal. After this, the dashboard will be at `https://your.domain.com`.

---

### Viewing logs

```bash
# Discord bot — live tail
journalctl -u kaluxhost-bot -f

# API server — live tail
journalctl -u kaluxhost-api -f

# Last 100 lines of either
journalctl -u kaluxhost-bot -n 100
journalctl -u kaluxhost-api -n 100

# nginx access/error logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

### Updating the platform

After pushing new code to your repo or uploading new files via SFTP:

```bash
cd /opt/kaluxhost

# Pull latest code (if using git)
git pull

# If Python requirements changed
.venv/bin/pip install -r requirements.txt

# If Node packages changed
pnpm install

# Rebuild dashboard if any dashboard files changed
cd artifacts/dashboard
BASE_PATH=/ PORT=3000 pnpm build
cd /opt/kaluxhost

# Restart services
systemctl restart kaluxhost-bot kaluxhost-api

# Verify both are running
systemctl status kaluxhost-bot kaluxhost-api

# nginx doesn't need restarting unless you changed its config
```

---

### Keeping data safe

All persistent data lives in `data/kaluxhost.db` (SQLite) and `data/transcripts/` (ticket text files).

```bash
# Create backup directory
mkdir -p /opt/backups/kaluxhost

# Manual backup
cp /opt/kaluxhost/data/kaluxhost.db \
   /opt/backups/kaluxhost/kaluxhost-$(date +%Y%m%d-%H%M).db

# Automated daily backup at 3 AM via cron
crontab -e
# Add this line:
0 3 * * * cp /opt/kaluxhost/data/kaluxhost.db /opt/backups/kaluxhost/kaluxhost-$(date +\%Y\%m\%d).db
```

To also back up transcripts:

```bash
# Add to cron alongside the database line:
0 3 * * * tar -czf /opt/backups/kaluxhost/transcripts-$(date +\%Y\%m\%d).tar.gz /opt/kaluxhost/data/transcripts/
```

---

### Quick-reference: service management

```bash
# Start / stop / restart
systemctl start kaluxhost-bot
systemctl stop kaluxhost-api
systemctl restart kaluxhost-bot kaluxhost-api

# Check status
systemctl status kaluxhost-bot
systemctl status kaluxhost-api

# Reload nginx after config changes
nginx -t && systemctl reload nginx
```

---

## 7. Environment Variables & Secrets

| Variable | Required | Description |
|---|---|---|
| `DISCORD_BOT_TOKEN` | ✅ Yes | Your bot token from discord.com/developers/applications |
| `JWT_SECRET` | ✅ Yes | Long random string — signs dashboard login tokens. Generate with `openssl rand -hex 48` |
| `API_PORT` | No | Port the API server listens on. Default: `3001` |

All other settings (prefix, ticket staff role, log channels, welcome messages, automod rules) are stored in the SQLite database and managed via bot commands or the dashboard.

### Getting a Discord Bot Token

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Create a new application → **Bot** tab → **Reset Token** → copy the token
3. Under **Privileged Gateway Intents**, enable all three:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
4. Under **OAuth2 → URL Generator**, select scopes: `bot` + `applications.commands`
5. Select bot permissions (minimum required):
   - View Channels, Send Messages, Embed Links, Attach Files, Read Message History
   - Manage Channels, Manage Messages
   - Add Reactions, Use External Emojis
   - Kick Members, Ban Members, Moderate Members
6. Copy the generated URL and use it to invite the bot to your server

---

## 8. Common Troubleshooting

### Bot won't start — "DISCORD_BOT_TOKEN is not set"
The token isn't being passed to the process. On a VPS check your `.env` file and the `EnvironmentFile=` line in the systemd service:
```bash
cat /opt/kaluxhost/.env          # verify the token is there
systemctl cat kaluxhost-bot      # verify EnvironmentFile= path is correct
systemctl restart kaluxhost-bot
journalctl -u kaluxhost-bot -n 20
```

### Dashboard shows a blank page or "cannot connect"
1. Check nginx is running: `systemctl status nginx`
2. Check the static files exist: `ls /opt/kaluxhost/artifacts/dashboard/dist/public/`
3. If the folder is empty, the build failed — re-run: `cd /opt/kaluxhost/artifacts/dashboard && BASE_PATH=/ PORT=3000 pnpm build`
4. Check nginx config is valid: `nginx -t`
5. Check nginx error log: `tail -30 /var/log/nginx/error.log`

### Dashboard loads but API calls fail (login doesn't work, tickets don't load)
The API server isn't running or nginx isn't proxying correctly.
```bash
# Check API server is up
systemctl status kaluxhost-api
journalctl -u kaluxhost-api -n 30

# Test the API directly on the server
curl http://localhost:3001/api/health
# Should return: {"ok":true}

# Test through nginx
curl http://your.domain.com/api/health
```
If the direct curl works but through nginx doesn't, check your nginx `location /api/` block.

### Dashboard login fails — "Invalid credentials"
The default admin account is `admin` / `admin123`. It is created automatically when the API server first starts if no admin exists. If the API server has never started, the account won't exist yet. Start the API service and try again.

### API server crashes with "JWT_SECRET is not set" or similar
Your `.env` file is missing `JWT_SECRET`. Add it and restart:
```bash
echo "JWT_SECRET=$(openssl rand -hex 48)" >> /opt/kaluxhost/.env
systemctl restart kaluxhost-api
```

### "An unexpected error occurred" on a bot command
Check the bot log for the real error:
```bash
journalctl -u kaluxhost-bot -n 50
```
Common causes:
- Missing database column — the bot auto-migrates on startup; restart it
- Discord permission issue — the bot's role needs the correct permissions

### Ticket transcript not available in the dashboard
Transcripts are only saved when a ticket is **deleted** via the "Delete Ticket" button in Discord (not just closed). The file is saved to `data/transcripts/`. If the file doesn't exist, the transcript was never saved.

### Slash commands not showing up in Discord
Slash commands sync at startup. It can take up to 1 hour for Discord to propagate them globally. Restart the bot and wait. To force-sync to your guild immediately, the bot already does this on startup for guild ID `1485175801887326339` — update that ID in `main/bot.py` if you're using a different guild.

### Bot keeps restarting on VPS
Check the journal for the crash reason:
```bash
journalctl -u kaluxhost-bot -n 50 --no-pager
```
Most common causes:
- Bad or expired Discord token
- Missing Python package — run `.venv/bin/pip install -r requirements.txt`
- Syntax error in a module — the error will name the file

### Ticket channels aren't created in the right category
Update `CATEGORY_MAP` in `modules/tickets.py` with your server's Discord category IDs. Right-click a category in Discord → Copy ID (enable Developer Mode in Discord Settings → Advanced first).

### Welcome messages not sending
1. Check `!welcomeconfig` — verify channel is set and status is enabled
2. Make sure the bot has **Send Messages** and **Embed Links** permission in that channel
3. Use `!testwelcome` to test manually without waiting for someone to join

### Staff can still message without claiming (admins)
This is by design — Discord administrators bypass all channel permission overwrites at the API level. The bot warns them in the channel when it detects this. Non-admin staff correctly cannot write until they claim.
