import { Router } from "express";
import { db } from "../lib/db.js";
import { requireAuth, requireAdmin } from "../lib/auth.js";
import { GUILD_ID } from "../lib/discord.js";

const router = Router();

router.get("/", requireAuth, (req, res) => {
  const settings = db.prepare("SELECT * FROM guild_settings WHERE guild_id = ?").get(GUILD_ID) as any;
  const ticketConfig = db.prepare("SELECT * FROM ticket_config WHERE guild_id = ?").get(GUILD_ID) as any;
  const automod = db.prepare("SELECT * FROM automod_settings WHERE guild_id = ?").get(GUILD_ID) as any;
  const logSettings = db.prepare("SELECT * FROM log_settings WHERE guild_id = ?").get(GUILD_ID) as any;

  res.json({
    prefix: settings?.prefix || "!",
    ticket_staff_role_id: ticketConfig?.staff_role_id || null,
    ticket_log_channel_id: ticketConfig?.log_channel_id || null,
    automod_banned_words: automod?.banned_words || "",
    automod_filter_links: automod?.filter_links || 0,
    automod_max_mentions: automod?.max_mentions || 5,
    log_channel_id: logSettings?.channel_id || null,
  });
});

router.patch("/", requireAdmin, (req, res) => {
  const {
    prefix,
    ticket_staff_role_id,
    ticket_log_channel_id,
    automod_banned_words,
    automod_filter_links,
    automod_max_mentions,
    log_channel_id,
  } = req.body as Record<string, any>;

  if (prefix !== undefined) {
    if (prefix.length > 5) { res.status(400).json({ error: "Prefix max 5 chars" }); return; }
    db.prepare(
      "INSERT INTO guild_settings (guild_id, prefix) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET prefix = excluded.prefix"
    ).run(GUILD_ID, prefix);
  }

  if (ticket_staff_role_id !== undefined || ticket_log_channel_id !== undefined) {
    const current = db.prepare("SELECT * FROM ticket_config WHERE guild_id = ?").get(GUILD_ID) as any;
    db.prepare(
      "INSERT INTO ticket_config (guild_id, staff_role_id, log_channel_id) VALUES (?,?,?) ON CONFLICT(guild_id) DO UPDATE SET staff_role_id=excluded.staff_role_id, log_channel_id=excluded.log_channel_id"
    ).run(GUILD_ID, ticket_staff_role_id ?? current?.staff_role_id ?? null, ticket_log_channel_id ?? current?.log_channel_id ?? null);
  }

  if (automod_banned_words !== undefined || automod_filter_links !== undefined || automod_max_mentions !== undefined) {
    const current = db.prepare("SELECT * FROM automod_settings WHERE guild_id = ?").get(GUILD_ID) as any;
    db.prepare(
      "INSERT INTO automod_settings (guild_id, banned_words, filter_links, max_mentions) VALUES (?,?,?,?) ON CONFLICT(guild_id) DO UPDATE SET banned_words=excluded.banned_words, filter_links=excluded.filter_links, max_mentions=excluded.max_mentions"
    ).run(
      GUILD_ID,
      automod_banned_words ?? current?.banned_words ?? "",
      automod_filter_links ?? current?.filter_links ?? 0,
      automod_max_mentions ?? current?.max_mentions ?? 5,
    );
  }

  if (log_channel_id !== undefined) {
    db.prepare(
      "INSERT INTO log_settings (guild_id, channel_id) VALUES (?,?) ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id"
    ).run(GUILD_ID, log_channel_id);
  }

  res.json({ success: true });
});

export default router;
