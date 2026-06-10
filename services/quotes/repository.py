from typing import Optional, Dict, Any, List

from core.database import db


class QuoteRepository:
    """
    Pure SQL repository.
    No business logic. No Discord dependencies.
    """

    # -------------------------
    # CREATE
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
            INSERT INTO quotes (
                guild_id,
                category,
                quote_text,
                author_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                guild_id,
                category.strip().lower(),
                text,
                author_id
            )
        )

        row = await db.fetchone(
            """
            SELECT last_insert_rowid() AS id
            """
        )

        return row["id"]

    # -------------------------
    # READ RANDOM
    # -------------------------

    async def get_random_quote(
        self,
        guild_id: int,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        if category:
            return await db.fetchone(
                """
                SELECT *
                FROM quotes
                WHERE guild_id = ?
                  AND category = ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (
                    guild_id,
                    category.strip().lower()
                )
            )

        return await db.fetchone(
            """
            SELECT *
            FROM quotes
            WHERE guild_id = ?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (guild_id,)
        )

    # -------------------------
    # CATEGORIES
    # -------------------------

    async def get_categories(
        self,
        guild_id: int
    ) -> List[str]:

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
    # DELETE
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
            (
                guild_id,
                quote_id
            )
        )

        if not row:
            return False

        await db.execute(
            """
            DELETE FROM quotes
            WHERE guild_id = ?
              AND id = ?
            """,
            (
                guild_id,
                quote_id
            )
        )

        return True