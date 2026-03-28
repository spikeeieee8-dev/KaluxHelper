import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(__dirname, "../../../../data/kaluxhost.db");

export const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
  CREATE TABLE IF NOT EXISTS web_accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL UNIQUE,
    password   TEXT    NOT NULL,
    role       TEXT    NOT NULL DEFAULT 'staff',
    discord_id TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
  );

  CREATE TABLE IF NOT EXISTS web_sessions (
    token      TEXT    PRIMARY KEY,
    account_id INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    FOREIGN KEY (account_id) REFERENCES web_accounts(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS bot_staff (
    guild_id TEXT NOT NULL,
    user_id  TEXT NOT NULL,
    role     TEXT NOT NULL DEFAULT 'staff',
    added_by TEXT,
    added_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    PRIMARY KEY (guild_id, user_id)
  );
`);

const adminCount = (db.prepare("SELECT COUNT(*) as c FROM web_accounts WHERE role='admin'").get() as { c: number }).c;
if (adminCount === 0) {
  const bcrypt = await import("bcryptjs");
  const hash = bcrypt.hashSync("admin123", 10);
  db.prepare("INSERT OR IGNORE INTO web_accounts (username, password, role) VALUES (?, ?, 'admin')")
    .run("admin", hash);
  console.log("Default admin account created: admin / admin123");
}
