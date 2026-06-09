import asyncio
import time
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Phase 10.2 Live UI Engine

    Adds:
    - persistent UI update loop
    - safe start/stop per guild
    """

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}
        self._ui_tasks: dict[int, asyncio.Task] = {}

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
    # IDLE DISCONNECT
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
    # UI LOOP (🔥 NEW CORE FEATURE)
    # =====================================================
    async def _ui_loop(self, guild_id: int, player: wavelink.Player):
        from services.music.player_message_manager import player_message_manager

        while True:
            try:
                state = music_manager.get_player(guild_id)

                if not state.current:
                    return

                guild = getattr(player, "guild", None)
                if guild:
                    await player_message_manager.update(guild)

                await asyncio.sleep(5)

            except Exception:
                return

    def _start_ui_loop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        if guild_id not in self._ui_tasks or self._ui_tasks[guild_id].done():
            self._ui_tasks[guild_id] = asyncio.create_task(
                self._ui_loop(guild_id, player)
            )

    def _stop_ui_loop(self, guild_id: int):
        task = self._ui_tasks.pop(guild_id, None)
        if task:
            task.cancel()

    # =====================================================
    # PLAY NEXT
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None

                self._stop_ui_loop(guild_id)

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

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

                # 🔥 START LIVE UI LOOP HERE
                self._start_ui_loop(player)

            except Exception:
                state.current = None
                await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):
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

        self._cancel_idle(guild_id)
        self._stop_ui_loop(guild_id)

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()