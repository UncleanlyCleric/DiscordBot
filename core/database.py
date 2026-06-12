import aiosqlite
from typing import Any, Optional, Sequence, Union
from pathlib import Path

from core.config import config


class Database:
    """
    Async SQLite wrapper.
    """

    def __init__(self):
        self.path = Path(config.db_path).resolve()
        self.conn: Optional[aiosqlite.Connection] = None
        print("[DB PATH FINAL]", self.path)
        self.db_path = Path(config.db_path).resolve()
        print("[MIGRATIONS DB]", self.db_path)

    async def connect(self):
        # Ensure directory exists
        db_path = Path(self.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"[DB] Using database at: {db_path.resolve()}")

        print(f"[DATABASE] DB PATH = {self.path}")
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA foreign_keys = ON;")
        await self.conn.commit()

        return self.conn

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def execute(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ):
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor   # IMPORTANT: needed for lastrowid

    async def fetchone(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ):
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ):
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # -------------------------
    # GUILD BOOTSTRAP
    # -------------------------

    async def ensure_guild(self, guild_id: int):
        await self.execute(
            "INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)",
            (guild_id,)
        )

        await self.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (guild_id,)
        )

        await self.execute(
            "INSERT OR IGNORE INTO music_state (guild_id) VALUES (?)",
            (guild_id,)
        )


# Singleton
db = Database()