import asyncio
import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:
    """
    Phase 10.1 Cleanup Engine (STABLE)

    Guarantees:
    - single event-driven playback path
    - safe skip fallback
    - no double advancement
    - idle disconnect safe
    """

    IDLE_TIMEOUT = 15
    SKIP_FALLBACK_TIMEOUT = 2

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}
        self._skip_guard: set[int] = set()
        self._play_token: dict[int, int] = {}

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
    # TOKEN SYSTEM
    # =====================================================
    def _next_token(self, guild_id: int) -> int:
        self._play_token[guild_id] = self._play_token.get(guild_id, 0) + 1
        return self._play_token[guild_id]

    # =====================================================
    # IDLE
    # =====================================================
    def _cancel_idle(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        await asyncio.sleep(self.IDLE_TIMEOUT)

        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        if state.current or state.queue.all():
            return

        try:
            await player.disconnect()
        except Exception:
            pass

    # =====================================================
    # UI NOTIFY (NEW CORE PIECE)
    # =====================================================
    async def _notify_ui(self, player: wavelink.Player):
        try:
            guild = getattr(player, "guild", None)
            if not guild:
                return

            state = music_manager.get_player(guild.id)

            if not state.player_channel_id:
                return

            from services.music.player_message_manager import player_message_manager

            await player_message_manager.update(guild)

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

            if not track:
                state.current = None

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                await self._notify_ui(player)
                return

            self._cancel_idle(guild_id)

            state.current = track
            self._next_token(guild_id)

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

                await self._notify_ui(player)

            except Exception:
                state.current = None
                await self._play_next(player)

    # =====================================================
    # TRACK END
    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        if guild_id in self._skip_guard:
            self._skip_guard.discard(guild_id)
            return

        await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        # mark skip so track_end doesn't double-fire logic
        self._skip_guard.add(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        # IMPORTANT: immediately force next track + UI
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

        await self._notify_ui(player)


engine = MusicEngine()