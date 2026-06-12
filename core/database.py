import os
import aiosqlite
from typing import Optional, Any, Sequence, Union


class Database:
    def __init__(self):
        self.path = os.getenv("DATABASE_PATH", "/app/storage/db/bot.db")
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        print(f"[DB] Connecting to: {self.path}")

        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA foreign_keys = ON;")
        await self.conn.commit()

        return self.conn

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def execute(self, query: str, params: Union[Sequence[Any], dict] = ()):
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor  # ✅ IMPORTANT FIX

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