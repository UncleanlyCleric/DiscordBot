from typing import List

from core.database import db
from services.music.models import Track


class MusicPersistence:
    """
    Restores queue + current track after bot restart.
    """

    async def load_queue(self, guild_id: int) -> List[Track]:
        rows = await db.fetchall(
            """
            SELECT track_title, track_author, track_uri, track_source, requester_id
            FROM music_queue
            WHERE guild_id = ?
            ORDER BY position ASC
            """,
            (guild_id,)
        )

        return [
            Track(
                title=r["track_title"],
                author=r["track_author"],
                uri=r["track_uri"],
                source=r["track_source"],
                requester_id=r["requester_id"]
            )
            for r in rows
        ]

    async def save_track(self, guild_id: int, position: int, track: Track):
        await db.execute(
            """
            INSERT INTO music_queue (
                guild_id, position, track_title,
                track_author, track_uri, track_source, requester_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                position,
                track.title,
                track.author,
                track.uri,
                track.source,
                track.requester_id
            )
        )

    async def clear(self, guild_id: int):
        await db.execute(
            """
            DELETE FROM music_queue
            WHERE guild_id = ?
            """,
            (guild_id,)
        )


music_persistence = MusicPersistence()