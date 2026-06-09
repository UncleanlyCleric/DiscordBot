import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 engine.

    Rules:
    - ONLY accepts wavelink.Player
    - NO discord imports
    - SINGLE SOURCE OF TRUTH for playback
    """

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}

        # Phase 7/8 stability systems
        self._playback_token: dict[int, int] = {}
        self._skip_lock: dict[int, bool] = {}

    # =====================================================
    # GUILD RESOLVE
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # LOCK
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # TOKEN (prevents race conditions)
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
    # CORE ENGINE
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            # skip guard (prevents double advancement)
            if self._skip_lock.pop(guild_id, False):
                return

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

            self._cancel_idle_timer(guild_id)

            state.current = track

            # token safety
            token = self._next_token(guild_id)
            state.play_token = token

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

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                state.current = None
                await self._play_next(player)

    # =====================================================
    # SKIP (FIXED — DO NOT DOUBLE-POP QUEUE)
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        # prevent race with track_end
        self._skip_lock[guild_id] = True

        state = music_manager.get_player(guild_id)
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

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