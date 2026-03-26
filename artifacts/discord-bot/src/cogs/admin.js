/**
 * ADMIN COG
 * Commands: setprefix, prefix, reload (prefix management)
 * Only prefix commands — these are admin-level server config tools
 */

import { PermissionFlagsBits, SlashCommandBuilder } from 'discord.js';
import { successEmbed, errorEmbed, brandEmbed } from '../utils/embed.js';
import { getPrefix, setPrefix } from '../utils/database.js';

const setPrefixCommand = {
  name: 'setprefix',
  aliases: ['changeprefix', 'prefix'],
  description: 'Change the bot prefix for this server',
  cog: 'Admin',

  async execute(message, args) {
    if (!message.member.permissions.has(PermissionFlagsBits.ManageGuild))
      return message.reply({ embeds: [errorEmbed('You need the **Manage Server** permission.')] });

    const newPrefix = args[0];
    if (!newPrefix)
      return message.reply({ embeds: [errorEmbed('Please provide a new prefix.\nExample: `!setprefix ?`')] });

    if (newPrefix.length > 5)
      return message.reply({ embeds: [errorEmbed('Prefix must be 5 characters or fewer.')] });

    setPrefix(message.guild.id, newPrefix);
    await message.reply({ embeds: [successEmbed(`Prefix changed to \`${newPrefix}\`\nTry it: \`${newPrefix}help\``)] });
  },
};

const currentPrefixCommand = {
  name: 'currentprefix',
  aliases: ['myprefix'],
  description: 'Show the current prefix',
  cog: 'Admin',

  async execute(message) {
    const prefix = getPrefix(message.guild.id);
    await message.reply({ embeds: [brandEmbed('📌 Current Prefix', `The current prefix is \`${prefix}\``)] });
  },
};

// Slash command to change prefix (admins only)
const slashSetPrefix = {
  data: new SlashCommandBuilder()
    .setName('setprefix')
    .setDescription('Change the command prefix for this server')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addStringOption((o) =>
      o.setName('prefix').setDescription('New prefix (max 5 chars)').setRequired(true),
    ),

  async execute(interaction) {
    const newPrefix = interaction.options.getString('prefix');
    if (newPrefix.length > 5)
      return interaction.reply({ embeds: [errorEmbed('Prefix must be 5 characters or fewer.')], ephemeral: true });

    setPrefix(interaction.guild.id, newPrefix);
    await interaction.reply({ embeds: [successEmbed(`Prefix changed to \`${newPrefix}\`\nTry it: \`${newPrefix}help\``)] });
  },
};

export default {
  setup(client) {
    client.commands.set(setPrefixCommand.name, setPrefixCommand);
    setPrefixCommand.aliases.forEach((a) => client.commands.set(a, setPrefixCommand));
    client.commands.set(currentPrefixCommand.name, currentPrefixCommand);
    currentPrefixCommand.aliases.forEach((a) => client.commands.set(a, currentPrefixCommand));

    client.slashCommands.set(slashSetPrefix.data.name, slashSetPrefix);
  },
};
