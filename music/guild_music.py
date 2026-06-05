import asyncio
import time
import random
import wavelink


class GuildMusic:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        self.queue: asyncio.Queue[wavelink.Playable] = asyncio.Queue()
        self.current: wavelink.Playable | None = None

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.last_active = time.time()

        # 📻 radio state
        self.radio_enabled = False
        self.radio_seed = None

    # ---------------- STATE ----------------
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.current is None and self.queue.empty()

    # ---------------- CONNECT ----------------
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        return self.player

    # ---------------- QUEUE ----------------
    async def add(self, track: wavelink.Playable):
        await self.queue.put(track)
        self.touch()

        if not self.current:
            await self.play_next()

    async def skip(self):
        if self.player:
            await self.player.stop()

    async def stop(self):
        if self.player:
            await self.player.disconnect()

        self.player = None
        self.current = None
        self.queue = asyncio.Queue()

    # ---------------- CORE PLAYER ----------------
    async def play_next(self):
        async with self.lock:
            if not self.player or not self.player.connected:
                return

            track = None

            # normal queue
            if not self.queue.empty():
                track = await self.queue.get()

            # radio fallback
            elif self.radio_enabled and self.radio_seed:
                results = await wavelink.Playable.search(self.radio_seed)
                if results:
                    track = random.choice(results[:10])

            if not track:
                self.current = None
                return

            self.current = track
            self.touch()

            await self.player.play(track)