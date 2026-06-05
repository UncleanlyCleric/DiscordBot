import asyncio
import time
import wavelink


class MusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue = asyncio.Queue()
        self.now_playing = None
        self.player: wavelink.Player | None = None

        self.last_active = time.time()
        self.lock = asyncio.Lock()

    # ---------------- STATE ----------------
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.now_playing is None and self.queue.empty()

    # ---------------- PLAYER SETUP ----------------
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        return self.player

    # ---------------- QUEUE ----------------
    async def add(self, track):
        await self.queue.put(track)
        self.touch()

    async def skip(self):
        if self.player:
            await self.player.stop()

    async def stop(self):
        if self.player:
            await self.player.disconnect()
        self.player = None

        # clear queue
        while not self.queue.empty():
            self.queue.get_nowait()

        self.now_playing = None

    # ---------------- PLAYBACK LOOP ----------------
    async def play_next(self):
        async with self.lock:
            if not self.player:
                return

            if self.queue.empty():
                self.now_playing = None
                return

            track = await self.queue.get()
            self.now_playing = track

            await self.player.play(track)