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

        # radio
        self.radio_enabled = False
        self.radio_seed = None

    # ---------------- STATE ----------------
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.now_playing is None and self.queue.empty()

    # ---------------- CONNECT ----------------
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        print("[DEBUG] Voice connected")
        return self.player

    # ---------------- ADD ----------------
    async def add(self, track):
        await self.queue.put(track)
        self.touch()

        print(f"[DEBUG] queued: {getattr(track, 'title', track)}")

        if not self.now_playing:
            await self.play_next()

    # ---------------- STOP ----------------
    async def stop(self):
        if self.player:
            await self.player.disconnect()

        self.player = None
        self.now_playing = None

        self.queue = asyncio.Queue()

    # ---------------- PLAYBACK ----------------
    async def play_next(self):
        async with self.lock:

            if not self.player:
                print("[DEBUG] No player")
                return

            track = None

            if not self.queue.empty():
                track = await self.queue.get()

            elif self.radio_enabled and self.radio_seed:
                results = await wavelink.Playable.search(self.radio_seed)
                if results:
                    track = random.choice(results[:10])

            if not track:
                self.now_playing = None
                return

            self.now_playing = track
            self.touch()

            print(f"[DEBUG] playing: {track.title}")

            try:
                await self.player.play(track)
            except Exception as e:
                print("[ERROR] play failed:", e)
                self.now_playing = None
                await self.play_next()