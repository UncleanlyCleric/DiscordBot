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
        # CORE STATE
        # =========================
        self.queue: asyncio.Queue[wavelink.Playable] = asyncio.Queue()
        self.history: list[wavelink.Playable] = []
        self.current: wavelink.Playable | None = None

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        # =========================
        # UI STATE
        # =========================
        self.message = None
        self.view = None

        # =========================
        # META
        # =========================
        self.last_active = time.time()

        self.radio_enabled = False
        self.radio_seed = None

    # =====================================================
    # STATE HELPERS
    # =====================================================
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.current is None and self.queue.empty()

    # =====================================================
    # SAFE QUEUE SNAPSHOT (NEW FOR UI PANEL V2)
    # =====================================================
    def get_queue_snapshot(self, limit: int = 10):
        """
        Returns a safe preview of upcoming queue items
        without modifying or consuming the queue.
        """

        try:
            items = list(self.queue._queue)  # internal deque
            return items[:limit]
        except Exception:
            return []

    # =====================================================
    # CONNECT
    # =====================================================
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        log.info(f"[Guild {self.guild_id}] connected")
        return self.player

    # =====================================================
    # ADD TRACK
    # =====================================================
    async def add(self, track: wavelink.Playable):
        self.touch()

        if not self.radio_seed:
            self.radio_seed = getattr(track, "author", None)

        await self.queue.put(track)

        if not self.current:
            await self.play_next()

    # =====================================================
    # PLAY NEXT
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

            if self.current:
                self.history.append(self.current)

            self.current = next_track
            self.touch()

            try:
                await self.player.play(next_track)
            except Exception as e:
                log.exception(f"play failed: {e}")
                self.current = None

    # =====================================================
    # PREVIOUS TRACK
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
            except Exception as e:
                log.exception(f"previous failed: {e}")
                return None

            return prev

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self):
        if self.player:
            await self.player.stop()

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self):
        self.touch()

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