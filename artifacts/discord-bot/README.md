# KaluxHost Discord Bot

A fully modular, cog-based Discord bot for the KaluxHost server.

## Features

- **Modular cogs** — add new modules by dropping a file in `src/cogs/`. Never touch existing code.
- **Dual command support** — both prefix (`!`) and slash (`/`) commands
- **Per-server prefix** — admins can change the prefix with `!setprefix <new>` or `/setprefix`
- **Persistent storage** — SQLite database stores settings and warnings across restarts

## Cogs (Modules)

| Cog | Commands |
|-----|----------|
| **Info** | help, ping, serverinfo, userinfo |
| **Moderation** | ban, kick, mute, unmute, warn, warnings, purge, slowmode |
| **Admin** | setprefix, currentprefix |
| **Hosting** | plans, uptime, status, support, ticket |

## Adding a New Cog

1. Create `src/cogs/my-cog.js`
2. Export a `default` object with a `setup(client)` function
3. Register prefix commands via `client.commands.set(name, cmd)`
4. Register slash commands via `client.slashCommands.set(name, cmd)`
5. The bot auto-loads all cog files — no other files need to change

```js
// src/cogs/my-cog.js
export default {
  setup(client) {
    client.commands.set('mycommand', {
      name: 'mycommand',
      cog: 'MyCog',
      async execute(message, args, client) {
        await message.reply('Hello from my cog!');
      },
    });
  },
};
```

## Setup

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DISCORD_BOT_TOKEN` | Your bot's token from Discord Developer Portal |
| `DISCORD_CLIENT_ID` | Your bot's Application ID (for slash command deploy) |
| `DISCORD_GUILD_ID` | *(Optional)* Guild ID for instant slash command deploy |

### Deploy Slash Commands

```bash
node src/deploy-commands.js
```

## Required Bot Permissions

- `Send Messages`
- `Read Message History`
- `Manage Messages`
- `Kick Members`
- `Ban Members`
- `Moderate Members`
- `Manage Channels`
- `View Channels`

Enable **Message Content Intent** in the Discord Developer Portal under Bot → Privileged Gateway Intents.
