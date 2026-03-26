/**
 * MODERATION COG
 * Commands: ban, kick, mute, unmute, warn, warnings, purge, slowmode
 * Supports both prefix (!) and slash (/) commands
 */

import { SlashCommandBuilder, PermissionFlagsBits } from 'discord.js';
import { successEmbed, errorEmbed, warnEmbed, brandEmbed } from '../utils/embed.js';
import { db } from '../utils/database.js';

// ─── Database Setup ───────────────────────────────────────────────────────────

db.exec(`
  CREATE TABLE IF NOT EXISTS warnings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id  TEXT NOT NULL,
    user_id   TEXT NOT NULL,
    mod_id    TEXT NOT NULL,
    reason    TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
  );
`);

// ─── Helpers ──────────────────────────────────────────────────────────────────

function hasPerms(member, perm) {
  return member.permissions.has(perm);
}

// ─── Prefix Commands ──────────────────────────────────────────────────────────

const banCommand = {
  name: 'ban',
  description: 'Ban a member',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.BanMembers))
      return message.reply({ embeds: [errorEmbed('You need the **Ban Members** permission.')] });

    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null);
    if (!member) return message.reply({ embeds: [errorEmbed('Member not found.')] });
    if (!member.bannable) return message.reply({ embeds: [errorEmbed('I cannot ban that member.')] });

    const reason = args.slice(1).join(' ') || 'No reason provided';
    await member.ban({ reason });
    await message.reply({ embeds: [successEmbed(`Banned **${member.user.tag}** — ${reason}`)] });
  },
};

const kickCommand = {
  name: 'kick',
  description: 'Kick a member',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.KickMembers))
      return message.reply({ embeds: [errorEmbed('You need the **Kick Members** permission.')] });

    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null);
    if (!member) return message.reply({ embeds: [errorEmbed('Member not found.')] });
    if (!member.kickable) return message.reply({ embeds: [errorEmbed('I cannot kick that member.')] });

    const reason = args.slice(1).join(' ') || 'No reason provided';
    await member.kick(reason);
    await message.reply({ embeds: [successEmbed(`Kicked **${member.user.tag}** — ${reason}`)] });
  },
};

const muteCommand = {
  name: 'mute',
  aliases: ['timeout'],
  description: 'Timeout a member (in minutes)',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.ModerateMembers))
      return message.reply({ embeds: [errorEmbed('You need the **Moderate Members** permission.')] });

    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null);
    if (!member) return message.reply({ embeds: [errorEmbed('Member not found.')] });

    const minutes = parseInt(args[1]) || 10;
    const reason = args.slice(2).join(' ') || 'No reason provided';
    await member.timeout(minutes * 60 * 1000, reason);
    await message.reply({ embeds: [successEmbed(`Muted **${member.user.tag}** for **${minutes}m** — ${reason}`)] });
  },
};

const unmuteCommand = {
  name: 'unmute',
  description: 'Remove timeout from a member',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.ModerateMembers))
      return message.reply({ embeds: [errorEmbed('You need the **Moderate Members** permission.')] });

    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null);
    if (!member) return message.reply({ embeds: [errorEmbed('Member not found.')] });

    await member.timeout(null);
    await message.reply({ embeds: [successEmbed(`Unmuted **${member.user.tag}**`)] });
  },
};

const warnCommand = {
  name: 'warn',
  description: 'Warn a member',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.ModerateMembers))
      return message.reply({ embeds: [errorEmbed('You need the **Moderate Members** permission.')] });

    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null);
    if (!member) return message.reply({ embeds: [errorEmbed('Member not found.')] });

    const reason = args.slice(1).join(' ') || 'No reason provided';
    db.prepare('INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?, ?, ?, ?)')
      .run(message.guild.id, member.id, message.author.id, reason);

    const count = db.prepare('SELECT COUNT(*) as c FROM warnings WHERE guild_id=? AND user_id=?')
      .get(message.guild.id, member.id).c;

    await message.reply({ embeds: [warnEmbed(`Warned **${member.user.tag}** — ${reason}\nTotal warnings: **${count}**`)] });

    await member.send(`⚠️ You have been warned in **${message.guild.name}**\nReason: ${reason}`).catch(() => {});
  },
};

const warningsCommand = {
  name: 'warnings',
  aliases: ['warns'],
  description: 'View warnings for a member',
  cog: 'Moderation',
  async execute(message, args) {
    const member = message.mentions.members.first()
      || await message.guild.members.fetch(args[0]).catch(() => null)
      || message.member;

    const rows = db.prepare('SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY created_at DESC LIMIT 10')
      .all(message.guild.id, member.id);

    const embed = brandEmbed(`⚠️ Warnings for ${member.user.tag}`)
      .setDescription(rows.length
        ? rows.map((w, i) => `**${i + 1}.** ${w.reason} — <@${w.mod_id}> <t:${w.created_at}:R>`).join('\n')
        : 'No warnings found.');

    await message.reply({ embeds: [embed] });
  },
};

const purgeCommand = {
  name: 'purge',
  aliases: ['clear', 'clean'],
  description: 'Bulk delete messages',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.ManageMessages))
      return message.reply({ embeds: [errorEmbed('You need the **Manage Messages** permission.')] });

    const amount = Math.min(parseInt(args[0]) || 10, 100);
    await message.channel.bulkDelete(amount + 1, true).catch(() => {});
    const confirm = await message.channel.send({ embeds: [successEmbed(`Deleted **${amount}** message(s).`)] });
    setTimeout(() => confirm.delete().catch(() => {}), 4000);
  },
};

const slowmodeCommand = {
  name: 'slowmode',
  description: 'Set channel slowmode (seconds)',
  cog: 'Moderation',
  async execute(message, args) {
    if (!hasPerms(message.member, PermissionFlagsBits.ManageChannels))
      return message.reply({ embeds: [errorEmbed('You need the **Manage Channels** permission.')] });

    const seconds = parseInt(args[0]) ?? 0;
    await message.channel.setRateLimitPerUser(seconds);
    await message.reply({ embeds: [successEmbed(`Slowmode set to **${seconds}s**`)] });
  },
};

// ─── Slash Commands ───────────────────────────────────────────────────────────

const slashBan = {
  data: new SlashCommandBuilder()
    .setName('ban')
    .setDescription('Ban a member')
    .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers)
    .addUserOption((o) => o.setName('user').setDescription('User to ban').setRequired(true))
    .addStringOption((o) => o.setName('reason').setDescription('Reason')),

  async execute(interaction) {
    const member = interaction.options.getMember('user');
    const reason = interaction.options.getString('reason') ?? 'No reason provided';
    if (!member?.bannable)
      return interaction.reply({ embeds: [errorEmbed('Cannot ban that member.')], ephemeral: true });
    await member.ban({ reason });
    await interaction.reply({ embeds: [successEmbed(`Banned **${member.user.tag}** — ${reason}`)] });
  },
};

const slashKick = {
  data: new SlashCommandBuilder()
    .setName('kick')
    .setDescription('Kick a member')
    .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers)
    .addUserOption((o) => o.setName('user').setDescription('User to kick').setRequired(true))
    .addStringOption((o) => o.setName('reason').setDescription('Reason')),

  async execute(interaction) {
    const member = interaction.options.getMember('user');
    const reason = interaction.options.getString('reason') ?? 'No reason provided';
    if (!member?.kickable)
      return interaction.reply({ embeds: [errorEmbed('Cannot kick that member.')], ephemeral: true });
    await member.kick(reason);
    await interaction.reply({ embeds: [successEmbed(`Kicked **${member.user.tag}** — ${reason}`)] });
  },
};

const slashMute = {
  data: new SlashCommandBuilder()
    .setName('mute')
    .setDescription('Timeout a member')
    .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers)
    .addUserOption((o) => o.setName('user').setDescription('User to mute').setRequired(true))
    .addIntegerOption((o) => o.setName('minutes').setDescription('Duration in minutes').setRequired(true))
    .addStringOption((o) => o.setName('reason').setDescription('Reason')),

  async execute(interaction) {
    const member = interaction.options.getMember('user');
    const minutes = interaction.options.getInteger('minutes');
    const reason = interaction.options.getString('reason') ?? 'No reason provided';
    await member.timeout(minutes * 60 * 1000, reason);
    await interaction.reply({ embeds: [successEmbed(`Muted **${member.user.tag}** for **${minutes}m** — ${reason}`)] });
  },
};

const slashWarn = {
  data: new SlashCommandBuilder()
    .setName('warn')
    .setDescription('Warn a member')
    .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers)
    .addUserOption((o) => o.setName('user').setDescription('User to warn').setRequired(true))
    .addStringOption((o) => o.setName('reason').setDescription('Reason')),

  async execute(interaction) {
    const member = interaction.options.getMember('user');
    const reason = interaction.options.getString('reason') ?? 'No reason provided';
    db.prepare('INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?, ?, ?, ?)')
      .run(interaction.guild.id, member.id, interaction.user.id, reason);
    const count = db.prepare('SELECT COUNT(*) as c FROM warnings WHERE guild_id=? AND user_id=?')
      .get(interaction.guild.id, member.id).c;
    await interaction.reply({ embeds: [warnEmbed(`Warned **${member.user.tag}** — ${reason}\nTotal warnings: **${count}**`)] });
    await member.send(`⚠️ You have been warned in **${interaction.guild.name}**\nReason: ${reason}`).catch(() => {});
  },
};

const slashPurge = {
  data: new SlashCommandBuilder()
    .setName('purge')
    .setDescription('Bulk delete messages')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages)
    .addIntegerOption((o) => o.setName('amount').setDescription('Number of messages (1-100)').setRequired(true)),

  async execute(interaction) {
    const amount = Math.min(interaction.options.getInteger('amount'), 100);
    await interaction.deferReply({ ephemeral: true });
    await interaction.channel.bulkDelete(amount, true);
    await interaction.editReply({ embeds: [successEmbed(`Deleted **${amount}** message(s).`)] });
  },
};

// ─── Setup ────────────────────────────────────────────────────────────────────

export default {
  setup(client) {
    const prefixCmds = [banCommand, kickCommand, muteCommand, unmuteCommand, warnCommand, warningsCommand, purgeCommand, slowmodeCommand];
    const slashCmds = [slashBan, slashKick, slashMute, slashWarn, slashPurge];

    for (const cmd of prefixCmds) client.commands.set(cmd.name, cmd);
    for (const cmd of slashCmds) client.slashCommands.set(cmd.data.name, cmd);
  },
};
