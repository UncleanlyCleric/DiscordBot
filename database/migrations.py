import aiosqlite
from pathlib import Path

from core.config import config


SCHEMA_PATH = Path("DiscordBot/database/schema.sql")


class MigrationRunner:
    """
    Responsible for:
    - initializing database schema
    - ensuring fresh installs work
    - future upgrade hooks (versioned migrations)
    """

    def __init__(self):
        self.db_path = config.get("database", "path")

    async def run(self):
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(
                f"Schema file not found: {SCHEMA_PATH}"
            )

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            await db.execute("PRAGMA foreign_keys = ON;")

            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

            # Split on semicolon safely for SQLite schema execution
            statements = [
                stmt.strip()
                for stmt in schema_sql.split(";")
                if stmt.strip()
            ]

            for stmt in statements:
                try:
                    await db.execute(stmt)
                except Exception as e:
                    # We don't hard-fail on "table already exists"
                    # because schema is idempotent
                    if "already exists" in str(e).lower():
                        continue
                    raise

            await db.commit()

        print("[DB] Migrations complete.")


migration_runner = MigrationRunner()