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

        print("=" * 60)
        print(f"[DB PATH FINAL] {self.path}")
        print("=" * 60)

    async def connect(self):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print("=" * 60)
        print(f"[APP DB] {self.path}")
        print(f"[DB EXISTS] {self.path.exists()}")
        print("=" * 60)

        self.conn = await aiosqlite.connect(
            str(self.path)
        )

        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute(
            "PRAGMA foreign_keys = ON;"
        )

        await self.conn.commit()

        # -------------------------------------------------
        # DEBUG: show tables actually present
        # -------------------------------------------------
        cursor = await self.conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        )

        tables = await cursor.fetchall()

        print("=" * 60)
        print("[APP TABLES]")
        for table in tables:
            print(f"  - {table['name']}")
        print("=" * 60)

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

            return (
                dict(row)
                if row else None
            )

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

            return [
                dict(r)
                for r in rows
            ]

    # -------------------------------------------------
    # GUILD BOOTSTRAP
    # -------------------------------------------------

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


# Singleton
db = Database()