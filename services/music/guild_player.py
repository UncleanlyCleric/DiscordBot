import asyncio
from typing import Optional

from services.music.queue import MusicQueue
from services.music.models import Track


class GuildPlayer:
    """
    PURE STATE ONLY.

    Rules:
    - NO playback logic
    - NO queue advancement
    - ONLY stores state used by engine
    """

    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        self.queue = MusicQueue()
        self.current: Optional[Track] = None

        self.lock = asyncio.Lock()

    # =====================================================
    # STATE MUTATION ONLY
    # =====================================================

    async def add(self, track: Track):
        async with self.lock:
            self.queue.add(track)

    async def clear(self):
        async with self.lock:
            self.queue.clear()
            self.current = None

    # =====================================================
    # SAFE SNAPSHOT (UI / DEBUG)
    # =====================================================

    def snapshot(self):
        return {
            "guild_id": self.guild_id,
            "current": self.current.title if self.current else None,
            "queue_size": len(self.queue),
        }