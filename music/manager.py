import asyncio
import time
import wavelink


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

    # ---------------- STATE ----------------
    def touch(self):
        self.last_active = time.time()

    def is_idle(self):
        return self.now_playing is None and self.queue.empty()

    # ---------------- CONNECT SAFETY ----------------
    async def connect(self, channel):
        if self.player:
            return self.player

        self.player = await channel.connect(cls=wavelink.Player)
        return self.player

    # ---------------- ADD TRACK ----------------
    async def add(self, track):
        self.touch()
        await self.queue.put(track)

        if not self.now_playing:
            await self.play_next()

    # ---------------- CORE PLAYBACK ----------------
    async def play_next(self):
        async with self.lock:

            if not self.player:
                return

            track = None

            if not self.queue.empty():
                track = await self.queue.get()

            if not track:
                self.now_playing = None
                return

            self.now_playing = track
            self.touch()

            try:
                await self.player.play(track)
            except Exception:
                self.now_playing = None
                await self.play_next()

    # =========================================================
    # 🔥 FIXED STOP (THIS IS WHAT YOUR UI WAS FAILING ON)
    # =========================================================
    async def stop(self):
        """
        Fully stops playback, clears queue, and disconnects safely.
        This MUST exist for UI button.
        """

        self.now_playing = None

        # clear queue safely
        self.queue = asyncio.Queue()

        # stop audio
        try:
            if self.player:
                await self.player.stop()
        except Exception:
            pass

        # disconnect voice
        try:
            if self.player:
                await self.player.disconnect()
        except Exception:
            pass

        self.player = None

        # optional UI cleanup
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass