import asyncio
import time
import logging
import wavelink
import random

log = logging.getLogger("music")


class MusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        self.queue = asyncio.Queue()

        self.now_playing = None
        self.history = []

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.message = None
        self.view = None

        self.last_active = time.time()

        self.radio_enabled = False
        self.radio_seed = None

        self.volume = 50

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

        try:
            await self.player.set_volume(self.volume)
        except Exception:
            pass

        return self.player

    # ---------------- ADD ----------------
    async def add(self, track, source="queue"):
        self.touch()

        if not self.radio_seed:
            self.radio_seed = getattr(track, "author", None)

        await self.queue.put((track, source))

        if not self.now_playing:
            await self.play_next()

    # ---------------- PLAY NEXT ----------------
    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            if self.queue.empty():
                self.now_playing = None
                return

            track, source = await self.queue.get()

            # 🔥 ALWAYS record history BEFORE overwrite
            if self.now_playing is not None:
                self.history.append(self.now_playing)

            self.now_playing = track
            self.touch()

            try:
                await self.player.play(track)
            except Exception as e:
                log.error(f"Play error: {e}")
                self.now_playing = None

    # ---------------- PREVIOUS TRACK ----------------
    async def play_previous(self):
        if not self.player:
            return None

        if not self.history:
            return None

        previous = self.history.pop()

        if self.now_playing:
            await self.queue.put((self.now_playing, "history"))

        self.now_playing = previous

        try:
            await self.player.play(previous)
        except Exception as e:
            log.error(f"Back play failed: {e}")
            return None

        return previous

    # ---------------- STOP ----------------
    async def stop(self):
        self.touch()

        self.now_playing = None
        self.queue = asyncio.Queue()
        self.history.clear()

        try:
            if self.player:
                await self.player.stop()
                await self.player.disconnect()
        except Exception:
            pass

        self.player = None

        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

    # ---------------- SHUFFLE ----------------
    async def shuffle(self):
        items = []

        while not self.queue.empty():
            items.append(await self.queue.get())

        random.shuffle(items)

        for i in items:
            await self.queue.put(i)

        return len(items)

    # ---------------- VOLUME (FIXED) ----------------
    async def set_volume(self, value: int):
        self.volume = max(0, min(100, value))

        if not self.player:
            return

        try:
            await self.player.set_volume(self.volume)
        except Exception:
            try:
                self.player.volume = self.volume
            except Exception:
                pass