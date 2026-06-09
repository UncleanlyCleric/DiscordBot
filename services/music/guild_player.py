import asyncio
from typing import Optional, List

from services.music.queue import MusicQueue
from services.music.models import Track


class GuildPlayer:
    """
    One instance per guild.

    Responsibilities:
    - queue management (single source of truth)
    - playback state
    - NO playback logic (handled by engine)
    """

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue = MusicQueue()

        self.current: Optional[Track] = None
        self.is_playing = False

        self.lock = asyncio.Lock()

    # -------------------------
    # QUEUE OPERATIONS
    # -------------------------

    async def add_track(self, track: Track):
        async with self.lock:
            self.queue.add(track)

    async def add_many(self, tracks: List[Track]):
        async with self.lock:
            self.queue.add_many(tracks)

    async def clear(self):
        async with self.lock:
            self.queue.clear()
            self.current = None
            self.is_playing = False

    # -------------------------
    # STATE TRANSITION (ENGINE ONLY SHOULD CALL THESE)
    # -------------------------

    async def set_current(self, track: Optional[Track]):
        async with self.lock:
            self.current = track
            self.is_playing = track is not None

    async def pop_next(self) -> Optional[Track]:
        async with self.lock:
            track = self.queue.next()

            if track:
                self.current = track
                self.is_playing = True
            else:
                self.current = None
                self.is_playing = False

            return track

    # -------------------------
    # STATE ACCESS
    # -------------------------

    def get_state(self):
        return {
            "guild_id": self.guild_id,
            "is_playing": self.is_playing,
            "queue_size": len(self.queue),
            "current": self.current.title if self.current else None,
        }