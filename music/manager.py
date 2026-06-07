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

        self.player: wavelink.Player | None = None
        self.lock = asyncio.Lock()

        self.message = None
        self.view = None

        self.last_active = time.time()

        # autoplay / radio support
        self.radio_enabled = False
        self.radio_seed = None

        # =========================
        # 🔥 NEW: playback history
        # =========================
        self.history: list = []

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

        log.info(f"[Guild {self.guild_id}] Connected to voice channel")

        return self.player

    # ---------------- ADD TRACK ----------------
    async def add(self, track):
        self.touch()

        if not self.radio_seed:
            self.radio_seed = getattr(track, "author", None)

        await self.queue.put(track)

        log.info(
            f"[Guild {self.guild_id}] Queued: "
            f"{getattr(track, 'title', 'Unknown')}"
        )

        if not self.now_playing:
            await self.play_next()

    # ---------------- PLAY NEXT ----------------
    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            track = None

            if not self.queue.empty():
                track = await self.queue.get()

            if not track:
                self.now_playing = None
                log.info(f"[Guild {self.guild_id}] Queue empty")
                return

            # =========================================
            # 🔥 FIX: push current into history
            # =========================================
            if self.now_playing:
                self.history.append(self.now_playing)

            self.now_playing = track
            self.touch()

            try:
                await self.player.play(track)

                log.info(
                    f"[Guild {self.guild_id}] Playing: "
                    f"{getattr(track, 'title', 'Unknown')}"
                )

            except Exception as e:
                log.exception(
                    f"[Guild {self.guild_id}] Failed to play track: {e}"
                )

                self.now_playing = None

    # ---------------- BACK (NEW) ----------------
    async def previous(self):
        """
        Play previous track from history safely.
        """
        if not self.history:
            return None

        if not self.player:
            return None

        prev = self.history.pop()

        # push current back into queue
        if self.now_playing:
            await self.queue.put(self.now_playing)

        self.now_playing = prev

        try:
            await self.player.play(prev)
            log.info(f"[Guild {self.guild_id}] Playing previous track")
        except Exception as e:
            log.exception(f"[Guild {self.guild_id}] Previous failed: {e}")
            return None

        return prev

    # ---------------- STOP ----------------
    async def stop(self):

        self.touch()
        self.now_playing = None

        self.queue = asyncio.Queue()
        self.radio_seed = None

        # clear history too
        self.history.clear()

        try:
            if self.player:
                await self.player.stop()
        except Exception:
            pass

        try:
            if self.player:
                await self.player.disconnect()
        except Exception:
            pass

        self.player = None

        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass

        log.info(f"[Guild {self.guild_id}] Playback stopped")

    # ---------------- SHUFFLE ----------------
    async def shuffle(self):

        tracks = []

        while not self.queue.empty():
            tracks.append(await self.queue.get())

        random.shuffle(tracks)

        for track in tracks:
            await self.queue.put(track)

        log.info(
            f"[Guild {self.guild_id}] Shuffled {len(tracks)} tracks"
        )

        return len(tracks)