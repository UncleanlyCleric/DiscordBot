import asyncio
import re
import sys
from pathlib import Path

from core.database import db


ABSTRACT_PATTERN = re.compile(
    r'bMotion_abstract_register\s+"([^"]+)"\s*\{(.*?)\}',
    re.DOTALL
)

ITEM_PATTERN = re.compile(
    r'"((?:[^"\\]|\\.)*)"'
)


class BMotionAbstractImporter:

    async def import_file(self, path: str):

        content = Path(path).read_text(
            encoding="utf-8",
            errors="ignore"
        )

        matches = ABSTRACT_PATTERN.findall(content)

        print(f"[IMPORT] Found {len(matches)} abstracts")

        imported_abstracts = 0
        imported_items = 0

        for abstract_name, body in matches:

            abstract_id = await self._upsert_abstract(
                abstract_name
            )

            items = ITEM_PATTERN.findall(body)

            for item in items:

                item = item.strip()

                if not item:
                    continue

                await db.execute(
                    """
                    INSERT INTO personality_abstract_items (
                        abstract_id,
                        text
                    )
                    VALUES (?, ?)
                    """,
                    (
                        abstract_id,
                        item
                    )
                )

                imported_items += 1

            imported_abstracts += 1

        print(
            f"[DONE] Imported "
            f"{imported_abstracts} abstracts, "
            f"{imported_items} items"
        )

    async def _upsert_abstract(
        self,
        name: str
    ) -> int:

        row = await db.fetchone(
            """
            SELECT id
            FROM personality_abstracts
            WHERE name = ?
            """,
            (name,)
        )

        if row:
            return row["id"]

        await db.execute(
            """
            INSERT INTO personality_abstracts (
                name
            )
            VALUES (?)
            """,
            (name,)
        )

        row = await db.fetchone(
            """
            SELECT id
            FROM personality_abstracts
            WHERE name = ?
            """,
            (name,)
        )

        return row["id"]


async def main():

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "python tools/import_bmotion_abstracts.py "
            "/path/to/abstracts.tcl"
        )
        return

    path = sys.argv[1]

    await db.connect()

    importer = BMotionAbstractImporter()

    await importer.import_file(path)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())