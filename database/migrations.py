import aiosqlite
from pathlib import Path

from core.config import config


class MigrationRunner:
    """
    Responsible for:
    - initializing database schema
    - ensuring fresh installs work
    - future upgrade hooks (versioned migrations)
    """

    def __init__(self):
        self.db_path = config.get("database", "path")

        # ✅ FIX: resolve schema path relative to THIS file
        # migrations.py -> /database/schema.sql
        self.base_dir = Path(__file__).resolve().parent
        self.schema_path = self.base_dir / "schema.sql"

    async def run(self):
        # -------------------------
        # Validate schema exists
        # -------------------------
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}"
            )

        # -------------------------
        # Connect DB
        # -------------------------
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            await db.execute("PRAGMA foreign_keys = ON;")

            schema_sql = self.schema_path.read_text(encoding="utf-8")

            # -------------------------
            # Execute schema safely
            # -------------------------
            statements = [
                stmt.strip()
                for stmt in schema_sql.split(";")
                if stmt.strip()
            ]

            for stmt in statements:
                try:
                    await db.execute(stmt)

                except Exception as e:
                    # idempotent schema handling
                    if "already exists" in str(e).lower():
                        continue
                    raise

            await db.commit()

        print("[DB] Migrations complete.")


migration_runner = MigrationRunner()