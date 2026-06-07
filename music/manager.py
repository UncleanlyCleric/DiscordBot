import asyncio
import time
import logging
import wavelink
import random

log = logging.getLogger("music")


class MusicManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

        # =========================
        # CORE STATE (SINGLE SOURCE OF TRUTH)
        # =========================
        self.queue: asyncio.Queue[wavelink.Playable] = asyncio.Queue()
        self.history: list[wavelink.Playable] = []
        self.current: wavelink.Playable | None = None

        # =========================
        # PLAYER
        # =========================
        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        # =========================
        # SETTINGS
        # =========================
        self.volume = 100
        self.radio_enabled = False
        self.radio_seed = None

        # =========================
        # UI STATE
        # =========================
        self.message = None
        self.view = None

        self.last_active = time.time()

    # =====================================================
    # STATE HELPERS
    # =====================================================
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.current is None and self.queue.empty()

    # =====================================================
    # VOLUME CONTROL (FIXED)
    # =====================================================
    async def set_volume(self, value: int):
        self.volume = max(0, min(100, value))

        if self.player:
            await self.player.set_volume(self.volume)

    async def volume_up(self):
        await self.set_volume(self.volume + 10)

    async def volume_down(self):
        await self.set_volume(self.volume - 10)

    # =====================================================
    # SAFE QUEUE VIEW
    # =====================================================
    def get_queue_snapshot(self, limit: int = 10):
        try:
            return list(self.queue._queue)[:limit]
        except Exception:
            return []

    # =====================================================
    # CONNECT
    # =====================================================
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        await self.player.set_volume(self.volume)

        log.info(f"[Guild {self.guild_id}] connected")
        return self.player

    # =====================================================
    # ADD TRACK
    # =====================================================
    async def add(self, track):
        self.touch()

        if not self.radio_seed:
            self.radio_seed = getattr(track, "author", None)

        await self.queue.put(track)

        if not self.current:
            await self.play_next()

    # =====================================================
    # PLAY NEXT (FIXED STATE FLOW)
    # =====================================================
    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            next_track = None

            if not self.queue.empty():
                next_track = await self.queue.get()

            elif self.radio_enabled and self.radio_seed:
                try:
                    results = await wavelink.Playable.search(self.radio_seed)
                    if results:
                        next_track = random.choice(results[:10])
                except Exception:
                    pass

            if not next_track:
                self.current = None
                return

            # push history BEFORE replacing current
            if self.current:
                self.history.append(self.current)

            self.current = next_track
            self.touch()

            try:
                await self.player.play(next_track)
                await self.player.set_volume(self.volume)
            except Exception as e:
                log.exception(f"play failed: {e}")
                self.current = None

    # =====================================================
    # PREVIOUS TRACK (FIXED)
    # =====================================================
    async def previous(self):
        async with self.lock:

            if not self.player or not self.history:
                return None

            prev = self.history.pop()

            if self.current:
                await self.queue.put(self.current)

            self.current = prev

            try:
                await self.player.play(prev)
                await self.player.set_volume(self.volume)
            except Exception:
                return None

            return prev

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self):
        if self.player:
            await self.player.stop()

    # =====================================================
    # STOP (FULL RESET)
    # =====================================================
    async def stop(self):
        self.current = None
        self.history.clear()
        self.queue = asyncio.Queue()
        self.radio_seed = None

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

    # =====================================================
    # SHUFFLE
    # =====================================================
    async def shuffle(self):
        items = []

        while not self.queue.empty():
            items.append(await self.queue.get())

        random.shuffle(items)

        for i in items:
            await self.queue.put(i)

        return len(items)