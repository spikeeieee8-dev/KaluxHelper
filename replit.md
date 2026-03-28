# KaluxHost Bot Platform

## Overview

Full-stack platform for the KaluxHost Discord Bot. Three main services:

1. **Discord Bot** (`bot.py` + `modules/`) — Python bot using discord.py
2. **API Server** (`artifacts/api-server/`) — Express.js REST API with JWT auth and SQLite
3. **Dashboard** (`artifacts/dashboard/`) — React frontend (public docs + staff dashboard)

## Services & Ports

| Service | Port | Workflow Name |
|---------|------|---------------|
| Discord Bot | — | KaluxHost Discord Bot |
| API Server | 3001 | KaluxHost API Server |
| Dashboard (Vite) | 23183 | artifacts/dashboard: web |

Dashboard proxies `/api/*` → API server on port 3001 via Vite's `server.proxy`.

## Default Credentials

- **Dashboard login**: `admin` / `admin123` (change immediately in Staff → your account)
- **Guild ID**: 1485175801887326339
- **Client ID**: 1485897092504354918

## Architecture

```
/              → Public Docs (all bot commands, searchable, user/admin filter)
/login         → Staff login
/dashboard     → Overview stats + charts
/dashboard/tickets      → Ticket management (close tickets, view history)
/dashboard/moderation   → Ban/kick/mute/warn GUI + warning lookup
/dashboard/staff        → Dashboard accounts + bot staff management
/dashboard/config       → Bot config (prefix, automod, ticket settings)
```

## Database

SQLite at `data/kaluxhost.db` — shared by both the bot (Python) and API server (Node.js).
WAL mode enabled for concurrent access.

Key tables:
- `web_accounts` — dashboard login accounts (id, username, password_hash, role, discord_id)
- `bot_staff` — Discord users with elevated bot command access (guild_id, user_id, role)
- `tickets` — support tickets
- `warnings` — moderation warnings
- `ticket_config`, `automod_settings`, `guild_settings` — bot configuration

## Bot Modules (24 loaded)

admin, automod, birthdays, counting, ghostping, giveaways, guard, hosting, info, invites, logs, moderation, music, panel, reviews, roles, socials, **staff**, starboard, stats, sticky, suggestions, tickets, verify

## Staff Bot Commands

```
!addstaff @user [role]    — Add Discord user to bot staff (admin only)
!removestaff @user        — Remove from bot staff (admin only)
!stafflist                — List all bot staff
!staffcheck [@user]       — Check if user is staff
/addstaff, /removestaff, /stafflist  — Slash command equivalents
```

## Two-Layer Staff System

1. **Discord Bot Staff** (`bot_staff` table): Discord users who can use admin bot commands
2. **Dashboard Accounts** (`web_accounts` table): Username/password accounts for the web dashboard

These are independent. A person can have one, both, or neither.

## Security Notes

- JWT tokens signed with `JWT_SECRET` env var (defaults to a hardcoded dev secret — set in prod)
- Passwords hashed with bcryptjs (cost factor 10)
- Admin-only endpoints enforce role check
- Staff can view but not edit config; only admins can change settings

## Running API Server

```bash
cd artifacts/api-server
node --import tsx/esm src/index.ts
```

Or use the `KaluxHost API Server` workflow.

## Stack

- **Discord Bot**: Python 3, discord.py 2.x, aiosqlite, yt-dlp (music)
- **API Server**: Node.js 20, Express 4, better-sqlite3, jsonwebtoken, bcryptjs
- **Dashboard**: React 19, Vite 7, Tailwind CSS v4, Recharts, wouter (routing)
- **Monorepo**: pnpm workspaces
