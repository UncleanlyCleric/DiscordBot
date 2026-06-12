import aiosqlite
import logging
from pathlib import Path

from core.config import config


class MigrationRunner:
    def __init__(self):
        self.db_path = Path(config.db_path).resolve()

        self.schema_path = (
            Path(__file__).resolve().parent / "schema.sql"
        )

    async def run(self):

        logging.info(
            "[MIGRATIONS] Starting (%s)",
            self.db_path
        )

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}"
            )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        async with aiosqlite.connect(self.db_path) as db:

            await db.execute(
                "PRAGMA foreign_keys = ON;"
            )

            schema_sql = self.schema_path.read_text(
                encoding="utf-8"
            )

            await db.executescript(schema_sql)
            await db.commit()

            cursor = await db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            )

            tables = [r[0] for r in await cursor.fetchall()]

        logging.info(
            "[MIGRATIONS] Complete. Tables=%s",
            tables
        )


migration_runner = MigrationRunner()