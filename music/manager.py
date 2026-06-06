import asyncio
import time
import logging
import wavelink

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

        log.info(
            f"[Guild {self.guild_id}] Connected to voice channel"
        )

        return self.player

    # ---------------- ADD TRACK ----------------
    async def add(self, track):
        self.touch()

        # seed autoplay from first track added
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

                log.info(
                    f"[Guild {self.guild_id}] Queue empty"
                )

                return

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

    # ---------------- STOP ----------------
    async def stop(self):
        """
        Fully stop playback,
        clear queue,
        disconnect voice,
        clean UI.
        """

        self.touch()

        self.now_playing = None

        # clear queue
        self.queue = asyncio.Queue()

        # reset autoplay state
        self.radio_seed = None

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

        log.info(
            f"[Guild {self.guild_id}] Playback stopped"
        )