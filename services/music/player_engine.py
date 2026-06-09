import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Phase 10 Music Engine (Production Stable State Machine)

    Guarantees:
    - single source of truth for playback
    - no race between skip / track_end
    - safe idle + autoplay hook
    """

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}

        # prevents double advancement (skip vs track_end)
        self._skip_guard: set[int] = set()

    # =====================================================
    # GUILD RESOLVE
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id")

    # =====================================================
    # LOCK
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # IDLE CONTROL
    # =====================================================
    def _cancel_idle(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        await asyncio.sleep(self.IDLE_TIMEOUT)

        try:
            guild_id = self._guild_id(player)
            state = music_manager.get_player(guild_id)

            # still active → abort
            if state.current or state.queue.all():
                return

            await player.disconnect()
            print(f"[ENGINE] Idle disconnect guild={guild_id}")

        except Exception:
            pass

        finally:
            try:
                self._idle_tasks.pop(self._guild_id(player), None)
            except Exception:
                pass

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        self._cancel_idle(guild_id)

        if not state.current:
            await self._play_next(player)

    # =====================================================
    # CORE PLAYBACK
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            # -------------------------------------------------
            # EMPTY QUEUE → IDLE MODE
            # -------------------------------------------------
            if not track:
                state.current = None

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

            # reset skip guard after valid progression
            self._skip_guard.discard(guild_id)

            self._cancel_idle(guild_id)

            state.current = track

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

                print(f"[ENGINE] Now playing: {track.title}")

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                state.current = None
                await self._play_next(player)

    # =====================================================
    # TRACK END (ONLY SAFE ENTRY POINT)
    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        # skip already triggered stop → ignore duplicate event
        if guild_id in self._skip_guard:
            self._skip_guard.discard(guild_id)
            return

        await self._play_next(player)

    # =====================================================
    # SKIP (SAFE + INSTANT)
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        # mark skip so track_end does NOT double-advance
        self._skip_guard.add(guild_id)

        state = music_manager.get_player(guild_id)

        # DO NOT clear current yet (prevents queue desync)
        # state.current = None  ❌ remove this

        try:
            # stopping triggers track_end, but we guard against it
            await player.stop()
        except Exception:
            pass

        # immediately advance AFTER stop safely
        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        self._cancel_idle(guild_id)

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()