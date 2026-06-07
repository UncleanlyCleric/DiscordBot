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

        # =========================
        # PLAYER
        # =========================
        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        # =========================
        # SETTINGS
        # =========================
        self.volume = 100

        # =========================
        # STATE
        # =========================
        self.last_active = time.time()

    # =====================================================
    # PLAYER BIND
    # =====================================================
    def bind_player(self, player: wavelink.Player):
        self.player = player
        self.touch()

    # =====================================================
    # STATE HELPERS
    # =====================================================
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.current is None and self.queue.empty()

    # =====================================================
    # VOLUME
    # =====================================================
    async def set_volume(self, value: int):
        self.volume = max(0, min(100, value))

        if self.player:
            await self.player.set_volume(self.volume)

    # =====================================================
    # QUEUE SNAPSHOT
    # =====================================================
    def get_queue_snapshot(self, limit: int = 10):
        return list(getattr(self.queue, "_queue", []))[:limit]

    # =====================================================
    # ADD TRACK
    # =====================================================
    async def add(self, track):
        self.touch()

        await self.queue.put(track)

        if not self.current:
            await self.play_next()

    # =====================================================
    # PLAY NEXT (AUTO FLOW CORE)
    # =====================================================
    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            next_track = None

            if not self.queue.empty():
                next_track = await self.queue.get()

            if not next_track:
                self.current = None
                return

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
    # SKIP
    # =====================================================
    async def skip(self):
        if self.player:
            await self.player.stop()

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self):

        self.current = None
        self.history.clear()

        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Exception:
                break

        try:
            if self.player:
                await self.player.stop()
                await self.player.disconnect()
        except Exception:
            pass

        self.player = None