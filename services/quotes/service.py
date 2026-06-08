import random
from typing import Optional, Dict, Any, List

from core.database import db


class QuoteService:
    """
    Pure business logic layer for quotes.
    No Discord code here.
    """

    # -------------------------
    # ADD QUOTE
    # -------------------------

    async def add_quote(
        self,
        guild_id: int,
        category: str,
        text: str,
        author_id: Optional[int] = None
    ) -> int:
        await db.execute(
            """
            INSERT INTO quotes (guild_id, category, quote_text, author_id)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, category.lower(), text, author_id)
        )

        row = await db.fetchone(
            """
            SELECT last_insert_rowid() AS id
            """
        )

        return row["id"]

    # -------------------------
    # RANDOM QUOTE
    # -------------------------

    async def get_random_quote(
        self,
        guild_id: int,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        if category:
            row = await db.fetchone(
                """
                SELECT *
                FROM quotes
                WHERE guild_id = ?
                AND category = ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (guild_id, category.lower())
            )
        else:
            row = await db.fetchone(
                """
                SELECT *
                FROM quotes
                WHERE guild_id = ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (guild_id,)
            )

        return row

    # -------------------------
    # CATEGORIES
    # -------------------------

    async def get_categories(self, guild_id: int) -> List[str]:
        rows = await db.fetchall(
            """
            SELECT DISTINCT category
            FROM quotes
            WHERE guild_id = ?
            ORDER BY category ASC
            """,
            (guild_id,)
        )

        return [r["category"] for r in rows]

    # -------------------------
    # DELETE QUOTE (NEW)
    # -------------------------

    async def delete_quote(
        self,
        guild_id: int,
        quote_id: int
    ) -> bool:

        row = await db.fetchone(
            """
            SELECT id
            FROM quotes
            WHERE guild_id = ?
            AND id = ?
            """,
            (guild_id, quote_id)
        )

        if not row:
            return False

        await db.execute(
            """
            DELETE FROM quotes
            WHERE guild_id = ?
            AND id = ?
            """,
            (guild_id, quote_id)
        )

        return True


quote_service = QuoteService()