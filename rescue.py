import asyncio
import aiosqlite

async def fix():
    # Use the path from your config or just "bot_data.db"
    async with aiosqlite.connect("bot_data.db") as db:
        # 1. Create the correct table if it's missing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                prefix TEXT NOT NULL DEFAULT '!'
            )""")
        
        # 2. Force the prefix to '!' for your specific server ID as a STRING
        server_id = "1485175801887326339"
        await db.execute("""
            INSERT INTO guild_settings (guild_id, prefix) 
            VALUES (?, ?) 
            ON CONFLICT(guild_id) DO UPDATE SET prefix = '!'
        """, (server_id, "!"))
        
        await db.commit()
    print(f"✅ Hard-reset prefix to '!' in guild_settings for ID: {server_id}")

if __name__ == "__main__":
    asyncio.run(fix())
