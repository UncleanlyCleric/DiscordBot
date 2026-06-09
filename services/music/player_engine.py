import asyncio
import time
import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:

    IDLE_TIMEOUT = 15
    UI_TICK = 5  # 🔥 live update interval

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}

        self._skip_guard: set[int] = set()

        self._ui_task: dict[int, asyncio.Task] = {}

    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)
        if guild:
            return guild.id
        raise RuntimeError("No guild")

    # =====================================================
    def _lock(self, guild_id: int):
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # UI LOOP (🔥 NEW CORE SYSTEM)
    # =====================================================
    async def _ui_loop(self, guild_id: int, player: wavelink.Player):

        while True:
            state = music_manager.get_player(guild_id)

            if not state.current:
                return

            try:
                await player_message_manager.update(player.guild)
            except Exception:
                pass

            await asyncio.sleep(self.UI_TICK)

    def _start_ui_loop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        if guild_id in self._ui_task:
            return

        self._ui_task[guild_id] = asyncio.create_task(
            self._ui_loop(guild_id, player)
        )

    def _stop_ui_loop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        task = self._ui_task.pop(guild_id, None)
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
                self._stop_ui_loop(player)
                return

            state.current = track
            state.current_started_at = time.time()

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

                self._start_ui_loop(player)

            except Exception:
                state.current = None
                await self._play_next(player)

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        state = music_manager.get_player(self._guild_id(player))
        state.queue.add(track)

        if not state.current:
            await self._play_next(player)

    # =====================================================
    # SKIP (instant)
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

        state = music_manager.get_player(self._guild_id(player))

        state.queue.clear()
        state.current = None

        self._stop_ui_loop(player)

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()