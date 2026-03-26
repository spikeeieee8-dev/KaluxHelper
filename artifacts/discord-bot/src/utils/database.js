import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { mkdirSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const dataDir = join(__dirname, '..', 'data');
mkdirSync(dataDir, { recursive: true });

const db = new Database(join(dataDir, 'kaluxhost.db'));

// Initialize tables
db.exec(`
  CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id TEXT PRIMARY KEY,
    prefix    TEXT NOT NULL DEFAULT '!'
  );
`);

const DEFAULT_PREFIX = '!';

export function getPrefix(guildId) {
  const row = db.prepare('SELECT prefix FROM guild_settings WHERE guild_id = ?').get(guildId);
  return row?.prefix ?? DEFAULT_PREFIX;
}

export function setPrefix(guildId, prefix) {
  db.prepare(`
    INSERT INTO guild_settings (guild_id, prefix)
    VALUES (?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET prefix = excluded.prefix
  `).run(guildId, prefix);
}

export { db };
