import aiosqlite
from pathlib import Path

from core.config import config


class MigrationRunner:
    def __init__(self):
        self.db_path = config.get("database", "path")

        self.schema_path = (
            Path(__file__).resolve().parent / "schema.sql"
        )

    async def run(self):

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}"
            )

        db_file = Path(self.db_path).resolve()

        print("=" * 60)
        print(f"[MIGRATION DB]      {db_file}")
        print(f"[SCHEMA FILE]       {self.schema_path}")
        print(f"[DB EXISTS BEFORE]  {db_file.exists()}")
        print("=" * 60)

        async with aiosqlite.connect(str(db_file)) as db:

            db.row_factory = aiosqlite.Row

            await db.execute(
                "PRAGMA foreign_keys = ON;"
            )

            schema_sql = self.schema_path.read_text(
                encoding="utf-8"
            )

            statements = [
                s.strip()
                for s in schema_sql.split(";")
                if s.strip()
            ]

            print(
                f"[MIGRATION] Executing {len(statements)} statements"
            )

            for stmt in statements:
                try:
                    await db.execute(stmt)

                except Exception as e:

                    if "already exists" in str(e).lower():
                        continue

                    print(
                        f"[MIGRATION ERROR]\n{stmt[:200]}"
                    )

                    raise

            await db.commit()

            cursor = await db.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            )

            tables = await cursor.fetchall()

            print("=" * 60)
            print("[MIGRATION TABLES]")
            for table in tables:
                print(f"  - {table['name']}")
            print("=" * 60)

        print("[DB] Migrations complete.")


migration_runner = MigrationRunner()