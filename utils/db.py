import aiosqlite
import os
from pathlib import Path

DB = Path(
    os.getenv(
        "QUOTES_DB_PATH",
        Path(__file__).resolve().parent.parent / "quotes.db"
    )
)


# ---------------- INIT ----------------
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


# ---------------- ADD ----------------
async def add(gid, cat, content, author):
    async with aiosqlite.connect(str(DB)) as db:
        await db.execute(
            "INSERT INTO quotes (guild_id, category, content, author) VALUES (?, ?, ?, ?)",
            (gid, cat, content, author)
        )
        await db.commit()


# ---------------- RANDOM (IMPROVED) ----------------
async def fetch_random(gid, cat):
    async with aiosqlite.connect(str(DB)) as db:
        async with db.execute(
            """
            SELECT id, content, category, author
            FROM quotes
            WHERE guild_id = ? AND category = ?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (gid, cat)
        ) as cur:
            row = await cur.fetchone()

    return row  # (id, content, category, author)


# ---------------- SEARCH ----------------
async def search(gid, query):
    async with aiosqlite.connect(str(DB)) as db:
        async with db.execute(
            """
            SELECT id, category, content, author
            FROM quotes
            WHERE guild_id = ?
            AND content LIKE ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (gid, f"%{query}%")
        ) as cur:
            return await cur.fetchall()


# ---------------- DELETE (NOW RETURNS SUCCESS) ----------------
async def delete(quote_id, gid):
    async with aiosqlite.connect(str(DB)) as db:
        cur = await db.execute(
            "DELETE FROM quotes WHERE id = ? AND guild_id = ?",
            (quote_id, gid)
        )
        await db.commit()
        return cur.rowcount > 0


# ---------------- EDIT (NOW RETURNS SUCCESS) ----------------
async def edit(quote_id, gid, new_content):
    async with aiosqlite.connect(str(DB)) as db:
        cur = await db.execute(
            """
            UPDATE quotes
            SET content = ?
            WHERE id = ? AND guild_id = ?
            """,
            (new_content, quote_id, gid)
        )
        await db.commit()
        return cur.rowcount > 0