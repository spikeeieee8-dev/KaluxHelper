import { EmbedBuilder } from 'discord.js';

const BRAND_COLOR = 0x5865F2; // KaluxHost brand purple-blue
const SUCCESS_COLOR = 0x57F287;
const ERROR_COLOR = 0xED4245;
const WARN_COLOR = 0xFEE75C;

export function brandEmbed(title, description) {
  return new EmbedBuilder()
    .setColor(BRAND_COLOR)
    .setTitle(title ?? null)
    .setDescription(description ?? null)
    .setFooter({ text: 'KaluxHost' })
    .setTimestamp();
}

export function successEmbed(description) {
  return new EmbedBuilder()
    .setColor(SUCCESS_COLOR)
    .setDescription(`✅ ${description}`)
    .setFooter({ text: 'KaluxHost' })
    .setTimestamp();
}

export function errorEmbed(description) {
  return new EmbedBuilder()
    .setColor(ERROR_COLOR)
    .setDescription(`❌ ${description}`)
    .setFooter({ text: 'KaluxHost' })
    .setTimestamp();
}

export function warnEmbed(description) {
  return new EmbedBuilder()
    .setColor(WARN_COLOR)
    .setDescription(`⚠️ ${description}`)
    .setFooter({ text: 'KaluxHost' })
    .setTimestamp();
}
