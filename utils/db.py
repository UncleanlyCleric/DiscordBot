import sqlite3
import asyncio
import random
import os

# -----------------------------------------------------
# DATA DIRECTORY ARCHITECTURE
# -----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "quotes.db")


# -----------------------------------------------------
# INIT
# -----------------------------------------------------
async def init():
    async with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()


# -----------------------------------------------------
# ADD QUOTE
# -----------------------------------------------------
async def add(guild_id: int, category: str, content: str, author_id: str):
    async with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            INSERT INTO quotes (guild_id, category, content, author)
            VALUES (?, ?, ?, ?)
        """, (str(guild_id), category.lower(), content, author_id))

        conn.commit()
        conn.close()


# -----------------------------------------------------
# FETCH RANDOM
# -----------------------------------------------------
async def fetch_random(guild_id: int, category: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT content FROM quotes
        WHERE guild_id = ? AND category = ?
    """, (str(guild_id), category.lower()))

    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    return random.choice(rows)[0]


# -----------------------------------------------------
# SEARCH
# -----------------------------------------------------
async def search(guild_id: int, query: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT id, category, content
        FROM quotes
        WHERE guild_id = ? AND content LIKE ?
    """, (str(guild_id), f"%{query}%"))

    results = c.fetchall()
    conn.close()

    return results


# -----------------------------------------------------
# DELETE
# -----------------------------------------------------
async def delete(quote_id: int, guild_id: int):
    async with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            DELETE FROM quotes
            WHERE id = ? AND guild_id = ?
        """, (quote_id, str(guild_id)))

        deleted = c.rowcount > 0

        conn.commit()
        conn.close()

        return deleted


# -----------------------------------------------------
# EDIT
# -----------------------------------------------------
async def edit(quote_id: int, guild_id: int, new_content: str):
    async with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            UPDATE quotes
            SET content = ?
            WHERE id = ? AND guild_id = ?
        """, (new_content, quote_id, str(guild_id)))

        updated = c.rowcount > 0

        conn.commit()
        conn.close()

        return updated