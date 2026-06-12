import aiosqlite
from pathlib import Path
import logging
from core.config import config


class MigrationRunner:
    def __init__(self):
        # Use the same path as Database()
        self.db_path = Path(config.db_path).resolve()

        self.schema_path = (
            Path(__file__).resolve().parent / "schema.sql"
        )

    async def run(self):

        logging.info("MIGRATION ENTERED")
        print("=" * 60)
        print("[MIGRATION START]")
        print("=" * 60)

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}"
            )

        print(f"[MIGRATION DB]      {self.db_path}")
        print(f"[SCHEMA FILE]       {self.schema_path}")
        print(f"[DB EXISTS BEFORE]  {self.db_path.exists()}")

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        async with aiosqlite.connect(self.db_path) as db:

            db.row_factory = aiosqlite.Row

            await db.execute(
                "PRAGMA foreign_keys = ON;"
            )

            schema_sql = self.schema_path.read_text(
                encoding="utf-8"
            )

            print(
                f"[SCHEMA SIZE]      {len(schema_sql)} bytes"
            )

            try:
                await db.executescript(schema_sql)
                await db.commit()

            except Exception:
                print("=" * 60)
                print("[MIGRATION FAILED]")
                print("=" * 60)
                raise

            cursor = await db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            )

            tables = await cursor.fetchall()

            print("=" * 60)
            print("[MIGRATION TABLES]")
            print("=" * 60)

            for table in tables:
                print(f"  - {table['name']}")

            print("=" * 60)

        print(f"[DB EXISTS AFTER]   {self.db_path.exists()}")
        print("[DB] Migrations complete.")
        print("=" * 60)


migration_runner = MigrationRunner()