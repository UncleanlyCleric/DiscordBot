import aiosqlite
from typing import Any, Optional, Sequence, Union

from core.config import config


class Database:
    """
    Async SQLite wrapper for the bot.
    """

    def __init__(self):
        self.path = config.get("database", "path")
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA foreign_keys = ON;")
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def execute(self, query: str, params: Union[Sequence[Any], dict] = ()):
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor  # IMPORTANT FIX

    async def fetchone(self, query: str, params: Union[Sequence[Any], dict] = ()):
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(self, query: str, params: Union[Sequence[Any], dict] = ()):
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ✅ THIS MUST EXIST
db = Database()