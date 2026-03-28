import { Router } from "express";
import { db } from "../lib/db.js";
import { requireAuth } from "../lib/auth.js";
import { discordPost, GUILD_ID } from "../lib/discord.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRANSCRIPTS_DIR = path.resolve(__dirname, "../../../../../data/transcripts");

const router = Router();

router.get("/", requireAuth, (req, res) => {
  const { status, page = "1", limit = "20", search = "" } = req.query as Record<string, string>;
  const offset = (parseInt(page) - 1) * parseInt(limit);

  let where = "guild_id = ?";
  const params: any[] = [GUILD_ID];

  if (status && status !== "all") {
    where += " AND status = ?";
    params.push(status);
  }

  if (search.trim()) {
    where += " AND (user_id LIKE ? OR claimed_by LIKE ? OR close_reason LIKE ?)";
    const like = `%${search.trim()}%`;
    params.push(like, like, like);
  }

  const countParams = [...params];
  const tickets = db.prepare(
    `SELECT * FROM tickets WHERE ${where} ORDER BY open_time DESC LIMIT ? OFFSET ?`
  ).all(...params, parseInt(limit), offset) as any[];

  const total = (db.prepare(
    `SELECT COUNT(*) as c FROM tickets WHERE ${where}`
  ).get(...countParams) as any).c;

  res.json({ tickets, total, page: parseInt(page), limit: parseInt(limit) });
});

router.get("/stats/summary", requireAuth, (req, res) => {
  const today = Math.floor(new Date().setHours(0, 0, 0, 0) / 1000);
  const week = today - 7 * 86400;

  const todayCount = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND open_time >= ?").get(GUILD_ID, today) as any).c;
  const weekCount = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND open_time >= ?").get(GUILD_ID, week) as any).c;
  const avgRating = (db.prepare("SELECT AVG(rating) as r FROM tickets WHERE guild_id = ? AND rating IS NOT NULL").get(GUILD_ID) as any).r || 0;
  const openCount = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND status = 'open'").get(GUILD_ID) as any).c;

  res.json({ todayCount, weekCount, avgRating: Math.round(avgRating * 10) / 10, openCount });
});

router.get("/:id", requireAuth, (req, res) => {
  const ticket = db.prepare("SELECT * FROM tickets WHERE id = ? AND guild_id = ?").get(req.params.id, GUILD_ID) as any;
  if (!ticket) { res.status(404).json({ error: "Ticket not found" }); return; }
  res.json(ticket);
});

router.get("/:id/transcript", requireAuth, (req, res) => {
  const ticket = db.prepare("SELECT * FROM tickets WHERE id = ? AND guild_id = ?").get(req.params.id, GUILD_ID) as any;
  if (!ticket) { res.status(404).json({ error: "Ticket not found" }); return; }

  const num = String(ticket.ticket_number).padStart(4, "0");
  const filePath = path.join(TRANSCRIPTS_DIR, `ticket-${num}-${GUILD_ID}.txt`);

  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: "Transcript not found. It may not have been saved yet." });
    return;
  }

  const content = fs.readFileSync(filePath, "utf-8");
  res.json({ content, ticket_number: ticket.ticket_number });
});

router.post("/:id/close", requireAuth, async (req, res) => {
  const { reason = "Closed from dashboard" } = req.body as { reason?: string };
  const ticket = db.prepare("SELECT * FROM tickets WHERE id = ? AND guild_id = ?").get(req.params.id, GUILD_ID) as any;
  if (!ticket) { res.status(404).json({ error: "Ticket not found" }); return; }
  if (ticket.status === "closed") { res.status(400).json({ error: "Already closed" }); return; }

  const now = Math.floor(Date.now() / 1000);
  db.prepare("UPDATE tickets SET status='closed', close_time=?, close_reason=? WHERE id=?")
    .run(now, reason, ticket.id);

  try {
    await discordPost(`/channels/${ticket.channel_id}/messages`, {
      embeds: [{
        title: "🔒 Ticket Closed",
        description: `Closed from dashboard by **${req.staff!.username}**\nReason: ${reason}`,
        color: 0xED4245,
      }]
    });
  } catch {}

  res.json({ success: true });
});

export default router;
