import asyncio
import time
import wavelink


class MusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        self.queue = asyncio.Queue()
        self.now_playing = None

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.message = None
        self.view = None

    async def add(self, track):
        # 🚨 SAFETY: block URLs entirely
        if isinstance(track, str) and "http" in track:
            return

        await self.queue.put(track)

        if not self.now_playing:
            await self.play_next()

    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            track = None

            if not self.queue.empty():
                track = await self.queue.get()

            if not track:
                self.now_playing = None
                return

            self.now_playing = track

            try:
                await self.player.play(track)
            except Exception:
                self.now_playing = None
                await self.play_next()