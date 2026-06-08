import aiosqlite
from typing import Any, Optional, Sequence, Union

from core.config import config


class Database:
    """
    Async SQLite wrapper for the bot.

    Responsibilities:
    - single shared connection
    - safe query helpers
    - row factory dict output
    - guild bootstrap support
    """

    def __init__(self):
        self.path = config.get("database", "path")
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA foreign_keys = ON;")
        await self.conn.commit()

        return self.conn

    async def close(self):
        if self.conn:
            await self.conn.close()

    # -------------------------
    # CORE EXECUTION METHODS
    # -------------------------

    async def execute(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ) -> None:
        if not self.conn:
            raise RuntimeError("Database not connected")

        await self.conn.execute(query, params)
        await self.conn.commit()

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
        """
        Ensures guild exists in DB and has default settings.
        Safe to call repeatedly.
        """

        await self.execute(
            """
            INSERT OR IGNORE INTO guilds (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )

        await self.execute(
            """
            INSERT OR IGNORE INTO guild_settings (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )

        await self.execute(
            """
            INSERT OR IGNORE INTO music_state (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )


# Global singleton
db = Database()