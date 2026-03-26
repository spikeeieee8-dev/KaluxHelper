/**
 * INFO COG
 * Commands: help, ping, serverinfo, userinfo
 * Supports both prefix (!) and slash (/) commands
 */

import { SlashCommandBuilder, EmbedBuilder } from 'discord.js';
import { brandEmbed, errorEmbed } from '../utils/embed.js';
import { getPrefix } from '../utils/database.js';

// ─── Command Definitions ─────────────────────────────────────────────────────

const helpCommand = {
  name: 'help',
  aliases: ['h', 'commands'],
  description: 'Show all available commands',

  async execute(message, args, client) {
    const prefix = getPrefix(message.guild.id);
    const embed = buildHelpEmbed(client, prefix);
    await message.reply({ embeds: [embed] });
  },
};

const pingCommand = {
  name: 'ping',
  description: 'Check bot latency',

  async execute(message, _args, client) {
    const latency = Date.now() - message.createdTimestamp;
    const wsLatency = client.ws.ping;
    const embed = brandEmbed('🏓 Pong!')
      .addFields(
        { name: 'Message Latency', value: `${latency}ms`, inline: true },
        { name: 'API Latency', value: `${wsLatency}ms`, inline: true },
      );
    await message.reply({ embeds: [embed] });
  },
};

const serverInfoCommand = {
  name: 'serverinfo',
  aliases: ['server', 'si'],
  description: 'Show server information',

  async execute(message) {
    const g = message.guild;
    await g.members.fetch();
    const embed = brandEmbed(`📋 ${g.name}`)
      .setThumbnail(g.iconURL({ dynamic: true }))
      .addFields(
        { name: 'Owner', value: `<@${g.ownerId}>`, inline: true },
        { name: 'Members', value: `${g.memberCount}`, inline: true },
        { name: 'Channels', value: `${g.channels.cache.size}`, inline: true },
        { name: 'Roles', value: `${g.roles.cache.size}`, inline: true },
        { name: 'Boost Level', value: `${g.premiumTier}`, inline: true },
        { name: 'Created', value: `<t:${Math.floor(g.createdTimestamp / 1000)}:R>`, inline: true },
      );
    await message.reply({ embeds: [embed] });
  },
};

const userInfoCommand = {
  name: 'userinfo',
  aliases: ['user', 'ui', 'whois'],
  description: 'Show user information',

  async execute(message, args) {
    const member = message.mentions.members.first()
      || (args[0] ? await message.guild.members.fetch(args[0]).catch(() => null) : null)
      || message.member;

    if (!member) {
      return message.reply({ embeds: [errorEmbed('User not found.')] });
    }

    const roles = member.roles.cache
      .filter((r) => r.id !== message.guild.id)
      .sort((a, b) => b.position - a.position)
      .map((r) => r.toString())
      .slice(0, 10)
      .join(', ') || 'None';

    const embed = brandEmbed(`👤 ${member.user.tag}`)
      .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
      .addFields(
        { name: 'ID', value: member.id, inline: true },
        { name: 'Nickname', value: member.nickname ?? 'None', inline: true },
        { name: 'Joined Server', value: `<t:${Math.floor(member.joinedTimestamp / 1000)}:R>`, inline: true },
        { name: 'Account Created', value: `<t:${Math.floor(member.user.createdTimestamp / 1000)}:R>`, inline: true },
        { name: `Roles [${member.roles.cache.size - 1}]`, value: roles },
      );
    await message.reply({ embeds: [embed] });
  },
};

// ─── Slash Command Definitions ────────────────────────────────────────────────

const slashHelp = {
  data: new SlashCommandBuilder()
    .setName('help')
    .setDescription('Show all available commands'),

  async execute(interaction, client) {
    const prefix = getPrefix(interaction.guild.id);
    const embed = buildHelpEmbed(client, prefix);
    await interaction.reply({ embeds: [embed] });
  },
};

const slashPing = {
  data: new SlashCommandBuilder()
    .setName('ping')
    .setDescription('Check bot latency'),

  async execute(interaction, client) {
    const latency = Date.now() - interaction.createdTimestamp;
    const wsLatency = client.ws.ping;
    const embed = brandEmbed('🏓 Pong!')
      .addFields(
        { name: 'Message Latency', value: `${latency}ms`, inline: true },
        { name: 'API Latency', value: `${wsLatency}ms`, inline: true },
      );
    await interaction.reply({ embeds: [embed] });
  },
};

const slashServerInfo = {
  data: new SlashCommandBuilder()
    .setName('serverinfo')
    .setDescription('Show server information'),

  async execute(interaction) {
    const g = interaction.guild;
    await g.members.fetch();
    const embed = brandEmbed(`📋 ${g.name}`)
      .setThumbnail(g.iconURL({ dynamic: true }))
      .addFields(
        { name: 'Owner', value: `<@${g.ownerId}>`, inline: true },
        { name: 'Members', value: `${g.memberCount}`, inline: true },
        { name: 'Channels', value: `${g.channels.cache.size}`, inline: true },
        { name: 'Roles', value: `${g.roles.cache.size}`, inline: true },
        { name: 'Boost Level', value: `${g.premiumTier}`, inline: true },
        { name: 'Created', value: `<t:${Math.floor(g.createdTimestamp / 1000)}:R>`, inline: true },
      );
    await interaction.reply({ embeds: [embed] });
  },
};

const slashUserInfo = {
  data: new SlashCommandBuilder()
    .setName('userinfo')
    .setDescription('Show user information')
    .addUserOption((opt) =>
      opt.setName('user').setDescription('The user to look up').setRequired(false),
    ),

  async execute(interaction) {
    const member = interaction.options.getMember('user') ?? interaction.member;
    const roles = member.roles.cache
      .filter((r) => r.id !== interaction.guild.id)
      .sort((a, b) => b.position - a.position)
      .map((r) => r.toString())
      .slice(0, 10)
      .join(', ') || 'None';

    const embed = brandEmbed(`👤 ${member.user.tag}`)
      .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
      .addFields(
        { name: 'ID', value: member.id, inline: true },
        { name: 'Nickname', value: member.nickname ?? 'None', inline: true },
        { name: 'Joined Server', value: `<t:${Math.floor(member.joinedTimestamp / 1000)}:R>`, inline: true },
        { name: 'Account Created', value: `<t:${Math.floor(member.user.createdTimestamp / 1000)}:R>`, inline: true },
        { name: `Roles [${member.roles.cache.size - 1}]`, value: roles },
      );
    await interaction.reply({ embeds: [embed] });
  },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildHelpEmbed(client, prefix) {
  const prefixCmds = [...client.commands.values()];
  const slashCmds = [...client.slashCommands.values()];

  const grouped = {};
  for (const cmd of prefixCmds) {
    const cog = cmd.cog ?? 'General';
    if (!grouped[cog]) grouped[cog] = [];
    grouped[cog].push(`\`${prefix}${cmd.name}\``);
  }

  const embed = new EmbedBuilder()
    .setColor(0x5865F2)
    .setTitle('📖 KaluxHost Bot — Help')
    .setDescription(
      `Use \`${prefix}<command>\` or \`/<command>\` to run a command.\nSlash commands: ${slashCmds.map((c) => `\`/${c.data.name}\``).join(', ')}`,
    )
    .setFooter({ text: `KaluxHost | Prefix: ${prefix}` })
    .setTimestamp();

  for (const [cog, cmds] of Object.entries(grouped)) {
    embed.addFields({ name: `📦 ${cog}`, value: cmds.join(' ') });
  }

  return embed;
}

// ─── Setup ────────────────────────────────────────────────────────────────────

export default {
  setup(client) {
    const prefixCmds = [helpCommand, pingCommand, serverInfoCommand, userInfoCommand];
    const slashCmds = [slashHelp, slashPing, slashServerInfo, slashUserInfo];

    for (const cmd of prefixCmds) {
      cmd.cog = 'Info';
      client.commands.set(cmd.name, cmd);
    }
    for (const cmd of slashCmds) {
      client.slashCommands.set(cmd.data.name, cmd);
    }
  },
};
