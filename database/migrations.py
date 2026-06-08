import aiosqlite
from pathlib import Path

from core.config import config


class MigrationRunner:
    def __init__(self):
        self.db_path = config.get("database", "path")

        # FIXED: safe relative path
        self.schema_path = Path(__file__).resolve().parent / "schema.sql"

    async def run(self):
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON;")

            schema_sql = self.schema_path.read_text(encoding="utf-8")

            for stmt in [s.strip() for s in schema_sql.split(";") if s.strip()]:
                try:
                    await db.execute(stmt)
                except Exception as e:
                    if "already exists" in str(e).lower():
                        continue
                    raise

            await db.commit()

        print("[DB] Migrations complete.")


migration_runner = MigrationRunner()