import { Router } from "express";
import bcrypt from "bcryptjs";
import { db } from "../lib/db.js";
import { requireAuth, requireAdmin } from "../lib/auth.js";
import { discordGet, GUILD_ID } from "../lib/discord.js";

const router = Router();

router.get("/", requireAuth, (req, res) => {
  const accounts = db.prepare(
    "SELECT id, username, role, discord_id, created_at FROM web_accounts ORDER BY role DESC, username"
  ).all() as any[];
  res.json(accounts);
});

router.post("/", requireAdmin, (req, res) => {
  const { username, password, role = "staff", discord_id } = req.body as {
    username: string; password: string; role?: string; discord_id?: string;
  };
  if (!username || !password) { res.status(400).json({ error: "Username and password required" }); return; }
  if (!["admin", "staff", "moderator"].includes(role)) { res.status(400).json({ error: "Invalid role" }); return; }

  const exists = db.prepare("SELECT id FROM web_accounts WHERE username = ?").get(username);
  if (exists) { res.status(409).json({ error: "Username already exists" }); return; }

  const hash = bcrypt.hashSync(password, 10);
  const result = db.prepare(
    "INSERT INTO web_accounts (username, password, role, discord_id) VALUES (?, ?, ?, ?)"
  ).run(username, hash, role, discord_id || null) as any;

  res.status(201).json({ id: result.lastInsertRowid, username, role, discord_id: discord_id || null });
});

router.patch("/:id", requireAdmin, (req, res) => {
  const { role, discord_id, password } = req.body as { role?: string; discord_id?: string; password?: string };
  const account = db.prepare("SELECT * FROM web_accounts WHERE id = ?").get(req.params.id) as any;
  if (!account) { res.status(404).json({ error: "Account not found" }); return; }
  if (String(account.id) === String(req.staff!.id) && role && role !== account.role) {
    res.status(400).json({ error: "Cannot change your own role" }); return;
  }

  if (role) db.prepare("UPDATE web_accounts SET role = ? WHERE id = ?").run(role, req.params.id);
  if (discord_id !== undefined) db.prepare("UPDATE web_accounts SET discord_id = ? WHERE id = ?").run(discord_id, req.params.id);
  if (password) {
    const hash = bcrypt.hashSync(password, 10);
    db.prepare("UPDATE web_accounts SET password = ? WHERE id = ?").run(hash, req.params.id);
  }
  res.json({ success: true });
});

router.delete("/:id", requireAdmin, (req, res) => {
  if (String(req.params.id) === String(req.staff!.id)) {
    res.status(400).json({ error: "Cannot delete your own account" }); return;
  }
  const result = db.prepare("DELETE FROM web_accounts WHERE id = ?").run(req.params.id) as any;
  if (result.changes === 0) { res.status(404).json({ error: "Account not found" }); return; }
  res.json({ success: true });
});

router.get("/bot-staff", requireAuth, (req, res) => {
  const staff = db.prepare("SELECT * FROM bot_staff WHERE guild_id = ? ORDER BY added_at DESC").all(GUILD_ID) as any[];
  res.json(staff);
});

router.post("/bot-staff", requireAdmin, (req, res) => {
  const { user_id, role = "staff" } = req.body as { user_id: string; role?: string };
  if (!user_id) { res.status(400).json({ error: "user_id required" }); return; }

  db.prepare(
    "INSERT OR REPLACE INTO bot_staff (guild_id, user_id, role, added_by) VALUES (?, ?, ?, ?)"
  ).run(GUILD_ID, user_id, role, String(req.staff!.id));
  res.status(201).json({ success: true });
});

router.delete("/bot-staff/:user_id", requireAdmin, (req, res) => {
  db.prepare("DELETE FROM bot_staff WHERE guild_id = ? AND user_id = ?").run(GUILD_ID, req.params.user_id);
  res.json({ success: true });
});

router.get("/leaderboard", requireAuth, (req, res) => {
  const rows = db.prepare(
    "SELECT * FROM staff_stats WHERE guild_id = ? ORDER BY tickets_handled DESC LIMIT 10"
  ).all(GUILD_ID) as any[];
  res.json(rows);
});

export default router;
