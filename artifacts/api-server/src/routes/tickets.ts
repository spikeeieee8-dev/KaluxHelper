import { Router } from "express";
import { db } from "../lib/db.js";
import { requireAuth } from "../lib/auth.js";
import { discordPost, GUILD_ID } from "../lib/discord.js";

const router = Router();

router.get("/", requireAuth, (req, res) => {
  const { status, page = "1", limit = "20" } = req.query as Record<string, string>;
  const offset = (parseInt(page) - 1) * parseInt(limit);

  let query = "SELECT * FROM tickets WHERE guild_id = ?";
  const params: any[] = [GUILD_ID];

  if (status && status !== "all") {
    query += " AND status = ?";
    params.push(status);
  }

  query += " ORDER BY open_time DESC LIMIT ? OFFSET ?";
  params.push(parseInt(limit), offset);

  const tickets = db.prepare(query).all(...params) as any[];
  const total = (db.prepare(
    status && status !== "all"
      ? "SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND status = ?"
      : "SELECT COUNT(*) as c FROM tickets WHERE guild_id = ?"
  ).get(...(status && status !== "all" ? [GUILD_ID, status] : [GUILD_ID])) as any).c;

  res.json({ tickets, total, page: parseInt(page), limit: parseInt(limit) });
});

router.get("/:id", requireAuth, (req, res) => {
  const ticket = db.prepare("SELECT * FROM tickets WHERE id = ? AND guild_id = ?").get(req.params.id, GUILD_ID) as any;
  if (!ticket) { res.status(404).json({ error: "Ticket not found" }); return; }
  res.json(ticket);
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

router.get("/stats/summary", requireAuth, (req, res) => {
  const today = Math.floor(new Date().setHours(0, 0, 0, 0) / 1000);
  const week = today - 7 * 86400;

  const todayCount = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND open_time >= ?").get(GUILD_ID, today) as any).c;
  const weekCount = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND open_time >= ?").get(GUILD_ID, week) as any).c;
  const avgRating = (db.prepare("SELECT AVG(rating) as r FROM tickets WHERE guild_id = ? AND rating IS NOT NULL").get(GUILD_ID) as any).r || 0;

  res.json({ todayCount, weekCount, avgRating: Math.round(avgRating * 10) / 10 });
});

export default router;
