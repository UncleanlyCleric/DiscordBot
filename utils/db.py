import aiosqlite
import os
from pathlib import Path

DB = Path(os.getenv("QUOTES_DB_PATH", Path(__file__).resolve().parent.parent / "quotes.db"))


async def init():
    DB.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB)) as db:
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
    DB.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB)) as db:
        await db.execute(
            "INSERT INTO quotes (guild_id, category, content, author) VALUES (?, ?, ?, ?)",
            (gid, cat, content, author)
        )
        await db.commit()


async def fetch_random(gid, cat):
    async with aiosqlite.connect(str(DB)) as db:
        async with db.execute(
            "SELECT content FROM quotes WHERE guild_id=? AND category=? ORDER BY RANDOM() LIMIT 1",
            (gid, cat)
        ) as cur:
            row = await cur.fetchone()

    return row[0] if row else None