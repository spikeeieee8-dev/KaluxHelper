"""
Async SQLite database helpers.
All tables are created on first access — no manual migration needed.
"""
import aiosqlite
from main.config import DB_PATH


async def _get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """Create all tables. Called once at bot startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id   TEXT PRIMARY KEY,
                prefix     TEXT NOT NULL DEFAULT '!'
            );

            CREATE TABLE IF NOT EXISTS warnings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id   TEXT    NOT NULL,
                user_id    TEXT    NOT NULL,
                mod_id     TEXT    NOT NULL,
                reason     TEXT    NOT NULL,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS module_states (
                module_name TEXT PRIMARY KEY,
                enabled     INTEGER NOT NULL DEFAULT 1
            );
        """)
        await db.commit()


# ── Prefix helpers ────────────────────────────────────────────────────────────

async def get_prefix(guild_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT prefix FROM guild_settings WHERE guild_id = ?", (str(guild_id),)
        ) as cur:
            row = await cur.fetchone()
            return row["prefix"] if row else "!"


async def set_prefix(guild_id: int, prefix: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO guild_settings (guild_id, prefix)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET prefix = excluded.prefix
        """, (str(guild_id), prefix))
        await db.commit()


# ── Warning helpers ───────────────────────────────────────────────────────────

async def add_warning(guild_id: int, user_id: int, mod_id: int, reason: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO warnings (guild_id, user_id, mod_id, reason) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), str(mod_id), reason),
        )
        await db.commit()
        async with db.execute(
            "SELECT COUNT(*) as c FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        ) as cur:
            row = await cur.fetchone()
            return row["c"]


async def get_warnings(guild_id: int, user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 15",
            (str(guild_id), str(user_id)),
        ) as cur:
            return await cur.fetchall()


async def clear_warnings(guild_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) as c FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        ) as cur:
            row = await cur.fetchone()
            count = row["c"]
        await db.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        await db.commit()
        return count
