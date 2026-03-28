import { Router } from "express";
import { db } from "../lib/db.js";
import { requireAuth } from "../lib/auth.js";
import { discordGet, GUILD_ID } from "../lib/discord.js";

const router = Router();

router.get("/", requireAuth, async (req, res) => {
  try {
    const totalTickets = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ?").get(GUILD_ID) as any).c;
    const openTickets = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND status = 'open'").get(GUILD_ID) as any).c;
    const closedTickets = (db.prepare("SELECT COUNT(*) as c FROM tickets WHERE guild_id = ? AND status = 'closed'").get(GUILD_ID) as any).c;
    const totalWarnings = (db.prepare("SELECT COUNT(*) as c FROM warnings WHERE guild_id = ?").get(GUILD_ID) as any).c;
    const totalStaff = (db.prepare("SELECT COUNT(*) as c FROM bot_staff WHERE guild_id = ?").get(GUILD_ID) as any).c;

    const recentTickets = db.prepare(
      "SELECT * FROM tickets WHERE guild_id = ? ORDER BY open_time DESC LIMIT 5"
    ).all(GUILD_ID) as any[];

    const topStaff = db.prepare(
      "SELECT * FROM staff_stats WHERE guild_id = ? ORDER BY tickets_handled DESC LIMIT 5"
    ).all(GUILD_ID) as any[];

    const ticketsByDay = db.prepare(`
      SELECT date(open_time, 'unixepoch') as day, COUNT(*) as count
      FROM tickets WHERE guild_id = ? AND open_time > strftime('%s','now','-7 days')
      GROUP BY day ORDER BY day
    `).all(GUILD_ID) as any[];

    let guildInfo: any = null;
    try {
      guildInfo = await discordGet(`/guilds/${GUILD_ID}?with_counts=true`);
    } catch (e) {
      console.error("Discord guild fetch failed:", e);
    }

    res.json({
      totalTickets,
      openTickets,
      closedTickets,
      totalWarnings,
      totalStaff,
      recentTickets,
      topStaff,
      ticketsByDay,
      guild: guildInfo ? {
        name: guildInfo.name,
        icon: guildInfo.icon,
        memberCount: guildInfo.approximate_member_count,
        onlineCount: guildInfo.approximate_presence_count,
        id: guildInfo.id,
      } : null,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch stats" });
  }
});

export default router;
