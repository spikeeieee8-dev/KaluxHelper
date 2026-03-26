/**
 * Deploy slash commands to Discord.
 * Run: node src/deploy-commands.js
 *
 * Set DISCORD_GUILD_ID in secrets to deploy to a specific server (instant).
 * Leave it unset to deploy globally (takes up to 1 hour to propagate).
 */

import { REST, Routes } from 'discord.js';
import { readdirSync } from 'fs';
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const token = process.env.DISCORD_BOT_TOKEN;
const clientId = process.env.DISCORD_CLIENT_ID;
const guildId = process.env.DISCORD_GUILD_ID; // optional — for guild-specific (instant) deploy

if (!token) throw new Error('DISCORD_BOT_TOKEN is not set.');
if (!clientId) throw new Error('DISCORD_CLIENT_ID is not set. Add your bot\'s Application ID as a secret.');

const commands = [];

const cogsPath = join(__dirname, 'cogs');
const cogFiles = readdirSync(cogsPath).filter((f) => f.endsWith('.js'));

for (const file of cogFiles) {
  const filePath = pathToFileURL(join(cogsPath, file)).href;
  const cog = await import(filePath);

  // Collect slash command data from each cog
  if (cog.default?.slashCommands) {
    for (const cmd of cog.default.slashCommands) {
      commands.push(cmd.data.toJSON());
    }
  }
}

// Also scan for slashCommands exported directly
// (our cogs use setup() so we need a dummy client)
import { Collection } from 'discord.js';
const fakeClient = { commands: new Collection(), slashCommands: new Collection() };
for (const file of cogFiles) {
  const filePath = pathToFileURL(join(cogsPath, file)).href;
  const cog = await import(filePath);
  if (cog.default?.setup) cog.default.setup(fakeClient);
}

const slashData = [...fakeClient.slashCommands.values()].map((c) => c.data.toJSON());

const rest = new REST({ version: '10' }).setToken(token);

try {
  console.log(`Deploying ${slashData.length} slash command(s)...`);

  if (guildId) {
    await rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: slashData });
    console.log(`✅ Deployed to guild ${guildId} (instant)`);
  } else {
    await rest.put(Routes.applicationCommands(clientId), { body: slashData });
    console.log('✅ Deployed globally (may take up to 1 hour to appear)');
  }
} catch (err) {
  console.error('❌ Failed to deploy:', err);
}
