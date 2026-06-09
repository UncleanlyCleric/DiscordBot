import asyncio
from typing import Optional

from services.music.queue import MusicQueue
from services.music.models import Track


class GuildPlayer:
    """
    One instance per guild.

    Responsibilities:
    - queue storage ONLY
    - playback state tracking ONLY
    - NO playback control (handled by player_engine)
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

    async def skip(self):
        """
        IMPORTANT:
        Skip MUST NOT advance the queue.
        Engine handles playback progression.

        We only reset state here.
        """
        async with self.lock:
            self.current = None
            self.is_playing = False
            return None

    async def clear(self):
        async with self.lock:
            self.queue.clear()
            self.current = None
            self.is_playing = False

    # -------------------------
    # STATE TRANSITIONS (ENGINE CONTROLLED)
    # -------------------------

    async def start(self):
        """
        DO NOT advance queue here anymore.
        Engine is the single source of truth.
        """
        async with self.lock:
            if self.current:
                return self.current

            return self.current

    async def _next_track(self):
        """
        DEPRECATED LOGIC (kept for compatibility but NOT USED)
        DO NOT CALL FROM ENGINE.
        """
        async with self.lock:
            self.current = self.queue.next()

            if not self.current:
                self.is_playing = False
                return None

            self.is_playing = True
            return self.current

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