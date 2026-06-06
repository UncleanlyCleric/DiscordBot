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
        self.history = []

        self.now_playing = None

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.message = None
        self.view = None

        self.last_active = time.time()

        self.radio_enabled = False
        self.radio_seed = None

        # ✅ FIX: navigation control
        self.skip_lock = False

        # ✅ FIX: volume state
        self.volume = 100

    # ---------------- STATE ----------------
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.now_playing is None and self.queue.empty()

    # ---------------- VOLUME ----------------
    async def set_volume(self, value: int):
        self.volume = max(0, min(200, value))

        if self.player:
            try:
                await self.player.set_volume(self.volume)
            except Exception as e:
                log.warning(f"Volume set failed: {e}")

    # ---------------- ADD ----------------
    async def add(self, track):
        self.touch()

        if not self.radio_seed:
            self.radio_seed = getattr(track, "author", None)

        await self.queue.put(track)

        if not self.now_playing:
            await self.play_next()

    # ---------------- PLAY NEXT ----------------
    async def play_next(self, from_back=False):
        async with self.lock:

            if not self.player:
                return

            # only push history if normal forward flow
            if self.now_playing and not from_back:
                self.history.append(self.now_playing)

            track = None

            if not self.queue.empty():
                track = await self.queue.get()

            if not track:
                self.now_playing = None
                return

            self.now_playing = track
            self.touch()

            try:
                self.skip_lock = True
                await self.player.play(track)
                await self.player.set_volume(self.volume)
            finally:
                self.skip_lock = False

    # ---------------- BACK ----------------
    async def play_previous(self):
        async with self.lock:

            if not self.history:
                return None

            prev = self.history.pop()

            # push current back into queue (front behavior approximated)
            if self.now_playing:
                await self.queue.put(self.now_playing)

            self.now_playing = prev

            try:
                self.skip_lock = True
                await self.player.play(prev)
                await self.player.set_volume(self.volume)
            finally:
                self.skip_lock = False

            return prev

    # ---------------- STOP ----------------
    async def stop(self):
        self.history.clear()
        self.queue = asyncio.Queue()
        self.now_playing = None

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