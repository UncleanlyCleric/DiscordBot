import aiosqlite

DB = "quotes.db"

async def init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            category TEXT,
            content TEXT,
            author TEXT
        )
        """)
        await db.commit()


async def add(gid, cat, content, author):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO quotes VALUES (NULL, ?, ?, ?, ?)",
            (gid, cat, content, author)
        )
        await db.commit()


async def fetch_random(gid, cat):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT content FROM quotes WHERE guild_id=? AND category=?",
            (gid, cat)
        ) as cur:
            rows = await cur.fetchall()

    return rows