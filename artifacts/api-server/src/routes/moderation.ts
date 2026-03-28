import { Router } from "express";
import { db } from "../lib/db.js";
import { requireAuth } from "../lib/auth.js";
import { discordPost, discordPut, discordDelete, discordGet, discordPatch, GUILD_ID } from "../lib/discord.js";

const router = Router();

router.get("/warnings/:user_id", requireAuth, (req, res) => {
  const warnings = db.prepare(
    "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC"
  ).all(GUILD_ID, req.params.user_id) as any[];
  res.json(warnings);
});

router.get("/warnings", requireAuth, (req, res) => {
  const { page = "1", limit = "20" } = req.query as Record<string, string>;
  const offset = (parseInt(page) - 1) * parseInt(limit);
  const warnings = db.prepare(
    "SELECT * FROM warnings WHERE guild_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
  ).all(GUILD_ID, parseInt(limit), offset) as any[];
  const total = (db.prepare("SELECT COUNT(*) as c FROM warnings WHERE guild_id = ?").get(GUILD_ID) as any).c;
  res.json({ warnings, total });
});

router.post("/ban", requireAuth, async (req, res) => {
  const { user_id, reason = "Banned from dashboard", delete_days = 0 } = req.body as {
    user_id: string; reason?: string; delete_days?: number;
  };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }
  try {
    await discordPut(`/guilds/${GUILD_ID}/bans/${user_id}`, {
      reason,
      delete_message_days: Math.min(delete_days, 7),
    });
    db.prepare("INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?,?,?,?)")
      .run(GUILD_ID, user_id, "dashboard", `[BAN] ${reason}`);
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.delete("/ban/:user_id", requireAuth, async (req, res) => {
  try {
    await discordDelete(`/guilds/${GUILD_ID}/bans/${req.params.user_id}`);
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/kick", requireAuth, async (req, res) => {
  const { user_id, reason = "Kicked from dashboard" } = req.body as { user_id: string; reason?: string };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }
  try {
    await discordDelete(`/guilds/${GUILD_ID}/members/${user_id}`);
    db.prepare("INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?,?,?,?)")
      .run(GUILD_ID, user_id, "dashboard", `[KICK] ${reason}`);
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/mute", requireAuth, async (req, res) => {
  const { user_id, minutes = 10, reason = "Muted from dashboard" } = req.body as {
    user_id: string; minutes?: number; reason?: string;
  };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }
  try {
    const until = new Date(Date.now() + minutes * 60 * 1000).toISOString();
    await discordPatch(`/guilds/${GUILD_ID}/members/${user_id}`, {
      communication_disabled_until: until,
      reason,
    });
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/unmute", requireAuth, async (req, res) => {
  const { user_id } = req.body as { user_id: string };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }
  try {
    await discordPatch(`/guilds/${GUILD_ID}/members/${user_id}`, {
      communication_disabled_until: null,
    });
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/warn", requireAuth, (req, res) => {
  const { user_id, reason = "Warned from dashboard" } = req.body as { user_id: string; reason?: string };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }
  db.prepare("INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?,?,?,?)")
    .run(GUILD_ID, user_id, "dashboard", reason);
  const count = (db.prepare("SELECT COUNT(*) as c FROM warnings WHERE guild_id = ? AND user_id = ?").get(GUILD_ID, user_id) as any).c;
  res.json({ success: true, total_warnings: count });
});

router.delete("/warnings/:id", requireAuth, (req, res) => {
  db.prepare("DELETE FROM warnings WHERE id = ? AND guild_id = ?").run(req.params.id, GUILD_ID);
  res.json({ success: true });
});

router.get("/members", requireAuth, async (req, res) => {
  const { query } = req.query as { query?: string };
  try {
    const members = await discordGet(
      `/guilds/${GUILD_ID}/members/search?query=${encodeURIComponent(query || "")}&limit=25`
    );
    res.json(members);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
