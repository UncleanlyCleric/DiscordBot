from typing import Optional

from core.database import db


class MarkovService:
    """
    Core Markov control layer.

    Responsibilities:
    - guild enable/disable state
    - channel whitelist management
    - message ingestion
    - settings retrieval
    """

    # -------------------------
    # ENABLE / DISABLE STATE
    # -------------------------

    async def is_enabled(self, guild_id: int) -> bool:
        row = await db.fetchone(
            """
            SELECT markov_enabled
            FROM guild_settings
            WHERE guild_id = ?
            """,
            (guild_id,)
        )

        if not row:
            return True  # default safe behavior

        return bool(row["markov_enabled"])

    async def set_enabled(self, guild_id: int, enabled: bool):
        await db.execute(
            """
            UPDATE guild_settings
            SET markov_enabled = ?
            WHERE guild_id = ?
            """,
            (1 if enabled else 0, guild_id)
        )

    # -------------------------
    # CHANNEL WHITELIST
    # -------------------------

    async def is_channel_allowed(self, guild_id: int, channel_id: int) -> bool:
        row = await db.fetchone(
            """
            SELECT 1
            FROM markov_channels
            WHERE guild_id = ?
            AND channel_id = ?
            """,
            (guild_id, channel_id)
        )

        return row is not None

    async def add_channel(self, guild_id: int, channel_id: int):
        await db.execute(
            """
            INSERT OR IGNORE INTO markov_channels (guild_id, channel_id)
            VALUES (?, ?)
            """,
            (guild_id, channel_id)
        )

    async def remove_channel(self, guild_id: int, channel_id: int):
        await db.execute(
            """
            DELETE FROM markov_channels
            WHERE guild_id = ?
            AND channel_id = ?
            """,
            (guild_id, channel_id)
        )

    # -------------------------
    # MESSAGE INGESTION
    # -------------------------

    async def ingest(self, guild_id: int, channel_id: int, message: str):
        if not message:
            return

        # basic cleanup (avoid garbage training)
        message = message.strip()

        if len(message) < 2:
            return

        await db.execute(
            """
            INSERT INTO markov_messages (guild_id, channel_id, message)
            VALUES (?, ?, ?)
            """,
            (guild_id, channel_id, message)
        )

    # -------------------------
    # SETTINGS FETCH
    # -------------------------

    async def get_settings(self, guild_id: int):
        row = await db.fetchone(
            """
            SELECT *
            FROM guild_settings
            WHERE guild_id = ?
            """,
            (guild_id,)
        )

        # safe defaults if missing row
        if not row:
            return {
                "markov_enabled": 1,
                "markov_chance": 0.5,
                "markov_cooldown_minutes": 15,
                "markov_min_words": 3,
                "markov_max_words": 30,
            }

        return row


markov_service = MarkovService()