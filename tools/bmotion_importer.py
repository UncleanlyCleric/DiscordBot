import json
from typing import List, Dict, Any, Optional

from core.database import db


class BMotionImporter:
    """
    Imports parsed bMotion JSON into SQL personality system.
    """

    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    # -------------------------
    # MAIN ENTRY POINT
    # -------------------------

    async def import_file(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            await self._import_trigger(entry)

    # -------------------------
    # IMPORT SINGLE TRIGGER
    # -------------------------

    async def _import_trigger(self, entry: Dict[str, Any]):
        trigger_type = entry.get("trigger_type", "keyword")
        pattern = entry.get("pattern", "")
        probability = entry.get("probability", 1.0)
        responses = entry.get("responses", [])

        if not pattern:
            return

        # 1. Insert trigger
        result = await db.execute(
            """
            INSERT INTO personality_triggers (
                guild_id, trigger_type, pattern, probability
            )
            VALUES (?, ?, ?, ?)
            """,
            (self.guild_id, trigger_type, pattern, probability)
        )

        trigger_id = result.lastrowid

        # 2. Insert responses
        for r in responses:
            await db.execute(
                """
                INSERT INTO personality_responses (
                    trigger_id, text
                )
                VALUES (?, ?)
                """,
                (trigger_id, r)
            )

    # -------------------------
    # OPTIONAL: CLEAN IMPORT (NO DUPES)
    # -------------------------

    async def exists(self, pattern: str) -> Optional[int]:
        row = await db.fetchone(
            """
            SELECT id FROM personality_triggers
            WHERE guild_id = ?
              AND pattern = ?
            LIMIT 1
            """,
            (self.guild_id, pattern)
        )
        return row["id"] if row else None

    # -------------------------
    # SMART IMPORT (MERGE DUPES)
    # -------------------------

    async def import_file_deduped(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            pattern = entry.get("pattern")

            if not pattern:
                continue

            existing_id = await self.exists(pattern)

            if existing_id:
                # merge responses into existing trigger
                for r in entry.get("responses", []):
                    await db.execute(
                        """
                        INSERT INTO personality_responses (
                            trigger_id, text
                        )
                        VALUES (?, ?)
                        """,
                        (existing_id, r)
                    )
            else:
                await self._import_trigger(entry)


# -------------------------
# CLI TOOL
# -------------------------

if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 3:
        print("Usage: python bmotion_importer.py <guild_id> <file.json>")
        exit(1)

    guild_id = int(sys.argv[1])
    file_path = sys.argv[2]

    importer = BMotionImporter(guild_id)

    asyncio.run(importer.import_file_deduped(file_path))

    print("Import complete.")