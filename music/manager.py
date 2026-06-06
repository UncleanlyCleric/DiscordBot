import asyncio
import time
import random
import wavelink


class MusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        self.queue = asyncio.Queue()
        self.now_playing = None

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.last_active = time.time()

        # autoplay
        self.radio_enabled = False
        self.radio_seed = None

        # social
        self.skip_votes = set()

        # UI state
        self.message = None
        self.view = None

    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.now_playing is None and self.queue.empty()

    async def add(self, track):
        await self.queue.put(track)
        self.touch()

        if not self.now_playing:
            await self.play_next()

    async def stop(self):
        if self.player:
            await self.player.disconnect()

        self.player = None
        self.now_playing = None
        self.skip_votes.clear()
        self.queue = asyncio.Queue()

        self.message = None
        self.view = None

    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            track = None

            # normal queue
            if not self.queue.empty():
                track = await self.queue.get()

            # autoplay fallback
            elif self.radio_enabled and self.radio_seed:
                results = await wavelink.Playable.search(self.radio_seed)

                if results:
                    base = random.choice(results[:5])
                    related = await wavelink.Playable.search(base.title)

                    if related:
                        track = random.choice(related[:10])

            if not track:
                self.now_playing = None
                return

            self.now_playing = track
            self.touch()

            try:
                await self.player.play(track)
            except Exception as e:
                print("[PLAY ERROR]", e)
                self.now_playing = None
                await self.play_next()