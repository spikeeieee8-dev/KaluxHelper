import { Client, GatewayIntentBits, Collection, Events } from 'discord.js';
import { readdirSync } from 'fs';
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, join } from 'path';
import { getPrefix } from './utils/database.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildModeration,
  ],
});

client.commands = new Collection();
client.slashCommands = new Collection();

// ─── Load Cogs (modules) ──────────────────────────────────────────────────────
const cogsPath = join(__dirname, 'cogs');
const cogFiles = readdirSync(cogsPath).filter((f) => f.endsWith('.js'));

for (const file of cogFiles) {
  const filePath = pathToFileURL(join(cogsPath, file)).href;
  const cog = await import(filePath);

  if (cog.default?.setup) {
    cog.default.setup(client);
    console.log(`[COG] Loaded: ${file}`);
  } else {
    console.warn(`[COG] Skipped (no setup export): ${file}`);
  }
}

// ─── Slash Command Interaction Handler ───────────────────────────────────────
client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  const command = client.slashCommands.get(interaction.commandName);
  if (!command) return;

  try {
    await command.execute(interaction, client);
  } catch (err) {
    console.error(`[SLASH ERROR] ${interaction.commandName}:`, err);
    const reply = { content: 'Something went wrong running that command.', ephemeral: true };
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp(reply);
    } else {
      await interaction.reply(reply);
    }
  }
});

// ─── Prefix Command Message Handler ──────────────────────────────────────────
client.on(Events.MessageCreate, async (message) => {
  if (message.author.bot) return;
  if (!message.guild) return;

  const prefix = getPrefix(message.guild.id);

  if (!message.content.startsWith(prefix)) return;

  const args = message.content.slice(prefix.length).trim().split(/\s+/);
  const commandName = args.shift().toLowerCase();

  const command = client.commands.get(commandName)
    || client.commands.find((c) => c.aliases?.includes(commandName));

  if (!command) return;

  try {
    await command.execute(message, args, client);
  } catch (err) {
    console.error(`[PREFIX ERROR] ${commandName}:`, err);
    await message.reply('Something went wrong running that command.');
  }
});

// ─── Ready ────────────────────────────────────────────────────────────────────
client.once(Events.ClientReady, (c) => {
  console.log(`\n✅  KaluxHost Bot is online as ${c.user.tag}`);
  console.log(`📦  Loaded ${client.commands.size} prefix command(s)`);
  console.log(`⚡  Loaded ${client.slashCommands.size} slash command(s)\n`);
  c.user.setActivity('KaluxHost | !help', { type: 4 }); // CUSTOM
});

const token = process.env.DISCORD_BOT_TOKEN;
if (!token) throw new Error('DISCORD_BOT_TOKEN is not set.');

client.login(token);
