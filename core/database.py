import aiosqlite
import logging

from pathlib import Path
from typing import Any, Optional, Sequence, Union

from core.config import config


class Database:
    def __init__(self):
        self.path = Path(config.db_path).resolve()
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.conn = await aiosqlite.connect(
            self.path
        )

        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute(
            "PRAGMA foreign_keys = ON;"
        )

        await self.conn.commit()

        logging.info(
            "[DB] Connected (%s)",
            self.path
        )

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
            raise RuntimeError(
                "Database not connected"
            )

        cursor = await self.conn.execute(
            query,
            params
        )

        await self.conn.commit()

        return cursor

    async def fetchone(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ):
        if not self.conn:
            raise RuntimeError(
                "Database not connected"
            )

        async with self.conn.execute(
            query,
            params
        ) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None

    async def fetchall(
        self,
        query: str,
        params: Union[Sequence[Any], dict] = ()
    ):
        if not self.conn:
            raise RuntimeError(
                "Database not connected"
            )

        async with self.conn.execute(
            query,
            params
        ) as cursor:

            rows = await cursor.fetchall()

            return [dict(r) for r in rows]

    async def ensure_guild(
        self,
        guild_id: int
    ):
        await self.execute(
            """
            INSERT OR IGNORE INTO guilds
            (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )

        await self.execute(
            """
            INSERT OR IGNORE INTO guild_settings
            (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )

        await self.execute(
            """
            INSERT OR IGNORE INTO music_state
            (guild_id)
            VALUES (?)
            """,
            (guild_id,)
        )


db = Database()