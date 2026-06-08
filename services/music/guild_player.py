import asyncio
from typing import Optional

from services.music.queue import MusicQueue
from services.music.models import Track


class GuildPlayer:
    """
    One instance per guild.

    Responsibilities:
    - queue management
    - playback state
    - interaction with Lavalink (later)
    - autoplay trigger
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
        async with self.lock:
            return await self._next_track()

    async def clear(self):
        async with self.lock:
            self.queue.clear()
            self.current = None
            self.is_playing = False

    # -------------------------
    # PLAYBACK CORE
    # -------------------------

    async def start(self):
        async with self.lock:
            if self.is_playing:
                return

            await self._next_track()

    async def _next_track(self):
        self.current = self.queue.next()

        if not self.current:
            self.is_playing = False
            return None

        self.is_playing = True

        # NOTE:
        # Lavalink playback will be wired here later
        # For now this is the state machine

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