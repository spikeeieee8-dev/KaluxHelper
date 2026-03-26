/**
 * HOSTING COG — KaluxHost Themed
 * Commands: plans, uptime, status, support, ticket
 * Supports both prefix and slash commands
 */

import { SlashCommandBuilder, EmbedBuilder } from 'discord.js';
import { brandEmbed, successEmbed } from '../utils/embed.js';

const BRAND_COLOR = 0x5865F2;

// ─── Plans Data ───────────────────────────────────────────────────────────────

const PLANS = [
  { name: '⚡ Starter', ram: '2GB', cpu: '1 vCore', storage: '20GB SSD', price: '$2.99/mo', color: 0x57F287 },
  { name: '🚀 Pro', ram: '4GB', cpu: '2 vCores', storage: '50GB SSD', price: '$5.99/mo', color: 0x5865F2 },
  { name: '💎 Elite', ram: '8GB', cpu: '4 vCores', storage: '100GB SSD', price: '$9.99/mo', color: 0xFEE75C },
  { name: '👑 Dedicated', ram: '16GB+', cpu: '8+ vCores', storage: '250GB SSD', price: 'Custom', color: 0xED4245 },
];

// ─── Prefix Commands ──────────────────────────────────────────────────────────

const plansCommand = {
  name: 'plans',
  aliases: ['pricing', 'packages'],
  description: 'View KaluxHost hosting plans',
  cog: 'Hosting',

  async execute(message) {
    const embed = new EmbedBuilder()
      .setColor(BRAND_COLOR)
      .setTitle('🖥️ KaluxHost — Hosting Plans')
      .setDescription('Premium hosting with 99.9% uptime guarantee. All plans include DDoS protection & 24/7 support.')
      .setFooter({ text: 'KaluxHost | Visit our website to order!' })
      .setTimestamp();

    for (const plan of PLANS) {
      embed.addFields({
        name: plan.name,
        value: `RAM: \`${plan.ram}\`\nCPU: \`${plan.cpu}\`\nStorage: \`${plan.storage}\`\nPrice: **${plan.price}**`,
        inline: true,
      });
    }

    await message.reply({ embeds: [embed] });
  },
};

const uptimeCommand = {
  name: 'uptime',
  description: 'Check bot / service uptime',
  cog: 'Hosting',

  async execute(message, _args, client) {
    const ms = client.uptime;
    const embed = brandEmbed('📡 Uptime Status')
      .addFields(
        { name: '🤖 Bot Uptime', value: formatUptime(ms), inline: true },
        { name: '🟢 Service Status', value: 'All systems operational', inline: true },
        { name: '📶 API Latency', value: `${client.ws.ping}ms`, inline: true },
      );
    await message.reply({ embeds: [embed] });
  },
};

const statusCommand = {
  name: 'status',
  description: 'Check KaluxHost service status',
  cog: 'Hosting',

  async execute(message) {
    const services = [
      { name: 'Web Panel', status: '🟢 Online' },
      { name: 'Game Servers', status: '🟢 Online' },
      { name: 'VPS Nodes', status: '🟢 Online' },
      { name: 'Discord Bot', status: '🟢 Online' },
      { name: 'Billing System', status: '🟢 Online' },
    ];

    const embed = brandEmbed('📊 KaluxHost — Service Status')
      .setDescription(services.map((s) => `${s.status} **${s.name}**`).join('\n'));

    await message.reply({ embeds: [embed] });
  },
};

const supportCommand = {
  name: 'support',
  aliases: ['help-hosting'],
  description: 'Get support information',
  cog: 'Hosting',

  async execute(message) {
    const embed = brandEmbed('🎫 KaluxHost Support')
      .addFields(
        { name: '📩 Open a Ticket', value: 'Use `!ticket <issue>` or `/ticket` to open a support ticket', inline: false },
        { name: '💬 Live Chat', value: 'Check our website for live chat support', inline: true },
        { name: '📧 Email', value: 'support@kaluxhost.com', inline: true },
        { name: '⏱️ Response Time', value: 'Usually within 1 hour', inline: true },
      );
    await message.reply({ embeds: [embed] });
  },
};

const ticketCommand = {
  name: 'ticket',
  description: 'Open a support ticket',
  cog: 'Hosting',

  async execute(message, args) {
    if (!args.length)
      return message.reply({ embeds: [brandEmbed('Usage', '`!ticket <describe your issue>`')] });

    const issue = args.join(' ');
    const embed = new EmbedBuilder()
      .setColor(0x5865F2)
      .setTitle('🎫 Support Ticket Created')
      .setDescription(`**Issue:** ${issue}`)
      .addFields(
        { name: 'Submitted by', value: `${message.author.tag}`, inline: true },
        { name: 'User ID', value: message.author.id, inline: true },
        { name: 'Status', value: '🟡 Pending', inline: true },
      )
      .setFooter({ text: 'KaluxHost Support | A staff member will assist you shortly.' })
      .setTimestamp();

    await message.reply({ embeds: [successEmbed('Your support ticket has been submitted! Staff will assist you shortly.') ] });

    // Post to a ticket log channel if one exists named "ticket-log" or "mod-log"
    const logChannel = message.guild.channels.cache.find(
      (c) => ['ticket-log', 'mod-log', 'tickets'].includes(c.name),
    );
    if (logChannel) await logChannel.send({ embeds: [embed] });
  },
};

// ─── Slash Commands ───────────────────────────────────────────────────────────

const slashPlans = {
  data: new SlashCommandBuilder()
    .setName('plans')
    .setDescription('View KaluxHost hosting plans'),

  async execute(interaction) {
    const embed = new EmbedBuilder()
      .setColor(BRAND_COLOR)
      .setTitle('🖥️ KaluxHost — Hosting Plans')
      .setDescription('Premium hosting with 99.9% uptime guarantee. All plans include DDoS protection & 24/7 support.')
      .setFooter({ text: 'KaluxHost | Visit our website to order!' })
      .setTimestamp();

    for (const plan of PLANS) {
      embed.addFields({
        name: plan.name,
        value: `RAM: \`${plan.ram}\`\nCPU: \`${plan.cpu}\`\nStorage: \`${plan.storage}\`\nPrice: **${plan.price}**`,
        inline: true,
      });
    }

    await interaction.reply({ embeds: [embed] });
  },
};

const slashStatus = {
  data: new SlashCommandBuilder()
    .setName('status')
    .setDescription('Check KaluxHost service status'),

  async execute(interaction) {
    const services = [
      { name: 'Web Panel', status: '🟢 Online' },
      { name: 'Game Servers', status: '🟢 Online' },
      { name: 'VPS Nodes', status: '🟢 Online' },
      { name: 'Discord Bot', status: '🟢 Online' },
      { name: 'Billing System', status: '🟢 Online' },
    ];

    const embed = brandEmbed('📊 KaluxHost — Service Status')
      .setDescription(services.map((s) => `${s.status} **${s.name}**`).join('\n'));

    await interaction.reply({ embeds: [embed] });
  },
};

const slashTicket = {
  data: new SlashCommandBuilder()
    .setName('ticket')
    .setDescription('Open a support ticket')
    .addStringOption((o) =>
      o.setName('issue').setDescription('Describe your issue').setRequired(true),
    ),

  async execute(interaction) {
    const issue = interaction.options.getString('issue');
    const embed = new EmbedBuilder()
      .setColor(0x5865F2)
      .setTitle('🎫 Support Ticket Created')
      .setDescription(`**Issue:** ${issue}`)
      .addFields(
        { name: 'Submitted by', value: `${interaction.user.tag}`, inline: true },
        { name: 'User ID', value: interaction.user.id, inline: true },
        { name: 'Status', value: '🟡 Pending', inline: true },
      )
      .setFooter({ text: 'KaluxHost Support | A staff member will assist you shortly.' })
      .setTimestamp();

    await interaction.reply({ embeds: [successEmbed('Your ticket has been submitted! Staff will assist you shortly.')], ephemeral: true });

    const logChannel = interaction.guild.channels.cache.find(
      (c) => ['ticket-log', 'mod-log', 'tickets'].includes(c.name),
    );
    if (logChannel) await logChannel.send({ embeds: [embed] });
  },
};

const slashUptime = {
  data: new SlashCommandBuilder()
    .setName('uptime')
    .setDescription('Check bot uptime'),

  async execute(interaction, client) {
    const embed = brandEmbed('📡 Uptime Status')
      .addFields(
        { name: '🤖 Bot Uptime', value: formatUptime(client.uptime), inline: true },
        { name: '🟢 Service Status', value: 'All systems operational', inline: true },
        { name: '📶 API Latency', value: `${client.ws.ping}ms`, inline: true },
      );
    await interaction.reply({ embeds: [embed] });
  },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatUptime(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const d = Math.floor(h / 24);
  return `${d}d ${h % 24}h ${m % 60}m ${s % 60}s`;
}

// ─── Setup ────────────────────────────────────────────────────────────────────

export default {
  setup(client) {
    const prefixCmds = [plansCommand, uptimeCommand, statusCommand, supportCommand, ticketCommand];
    const slashCmds = [slashPlans, slashStatus, slashTicket, slashUptime];

    for (const cmd of prefixCmds) client.commands.set(cmd.name, cmd);
    for (const cmd of slashCmds) client.slashCommands.set(cmd.data.name, cmd);
  },
};
