import { Router } from "express";
import bcrypt from "bcryptjs";
import { db } from "../lib/db.js";
import { signToken, requireAuth } from "../lib/auth.js";

const router = Router();

router.post("/login", (req, res) => {
  const { username, password } = req.body as { username: string; password: string };
  if (!username || !password) {
    res.status(400).json({ error: "Username and password required" });
    return;
  }
  const account = db.prepare("SELECT * FROM web_accounts WHERE username = ?").get(username) as any;
  if (!account || !bcrypt.compareSync(password, account.password)) {
    res.status(401).json({ error: "Invalid credentials" });
    return;
  }
  const token = signToken({ id: account.id, username: account.username, role: account.role });
  res.json({ token, user: { id: account.id, username: account.username, role: account.role, discord_id: account.discord_id } });
});

router.get("/me", requireAuth, (req, res) => {
  const account = db.prepare("SELECT id, username, role, discord_id, created_at FROM web_accounts WHERE id = ?").get(req.staff!.id) as any;
  if (!account) { res.status(404).json({ error: "Account not found" }); return; }
  res.json(account);
});

router.post("/change-password", requireAuth, (req, res) => {
  const { current, newPassword } = req.body as { current: string; newPassword: string };
  const account = db.prepare("SELECT * FROM web_accounts WHERE id = ?").get(req.staff!.id) as any;
  if (!bcrypt.compareSync(current, account.password)) {
    res.status(401).json({ error: "Current password incorrect" });
    return;
  }
  const hash = bcrypt.hashSync(newPassword, 10);
  db.prepare("UPDATE web_accounts SET password = ? WHERE id = ?").run(hash, req.staff!.id);
  res.json({ success: true });
});

export default router;
