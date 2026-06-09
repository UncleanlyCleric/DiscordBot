import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 engine.

    Rules:
    - ONLY accepts wavelink.Player
    - NO discord imports
    - NO guild-based API usage
    """

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}

        # =========================
        # PHASE 7 ADDITIONS
        # =========================
        self._playback_token: dict[int, int] = {}
        self._skip_lock: dict[int, bool] = {}
        self.autoplay: dict[int, bool] = {}

    # =====================================================
    # SAFE GUILD RESOLVE
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # LOCK PER GUILD
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()

        return self._locks[guild_id]

    # =====================================================
    # TOKEN SYSTEM (PHASE 7 FIX)
    # =====================================================
    def _next_token(self, guild_id: int) -> int:
        self._playback_token[guild_id] = self._playback_token.get(guild_id, 0) + 1
        return self._playback_token[guild_id]

    # =====================================================
    # IDLE TIMER
    # =====================================================
    def _cancel_idle_timer(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)

        if task and not task.done():
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        await asyncio.sleep(self.IDLE_TIMEOUT)

        try:
            guild_id = self._guild_id(player)
            state = music_manager.get_player(guild_id)

            if state.current is not None:
                return

            if state.queue.all():
                return

            await player.disconnect()

        except Exception:
            pass

        finally:
            try:
                guild_id = self._guild_id(player)
                self._idle_tasks.pop(guild_id, None)
            except Exception:
                pass

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        self._cancel_idle_timer(guild_id)

        if not state.current:
            await self._play_next(player)

    # =====================================================
    # PUBLIC NEXT
    # =====================================================
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    # =====================================================
    # WATCHDOG (PHASE 7 FIX)
    # =====================================================
    async def _watchdog(self, player: wavelink.Player):
        while True:
            await asyncio.sleep(10)

            try:
                guild_id = self._guild_id(player)
                state = music_manager.get_player(guild_id)

                if state.current and not player.playing:
                    await self._play_next(player)

            except Exception:
                break

    # =====================================================
    # CORE ENGINE
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            # =========================
            # EMPTY QUEUE
            # =========================
            if not track:
                state.current = None

                if self.autoplay.get(guild_id):
                    return

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

            # cancel idle when playing
            self._cancel_idle_timer(guild_id)

            state.current = track

            # =========================
            # TOKEN (ANTI-RACE)
            # =========================
            token = self._next_token(guild_id)
            state.play_token = token

            # start watchdog once
            if not hasattr(player, "_watchdog_started"):
                player._watchdog_started = True
                asyncio.create_task(self._watchdog(player))

            try:
                playable = getattr(track, "playable", None)

                if not playable:
                    results = await wavelink.Playable.search(
                        track.uri or track.title
                    )

                    if not results:
                        return

                    playable = results[0]

                await player.play(playable)

            except Exception:
                state.current = None
                await self._play_next(player)

    # =====================================================
    # SKIP (FIXED)
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.current = None

        self._skip_lock[guild_id] = True

        try:
            await player.stop()
        except Exception:
            pass

        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        self._cancel_idle_timer(guild_id)

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()