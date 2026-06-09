import asyncio
import time
import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:
    """
    Stage 3.5 Engine (FULL OWNERSHIP MODEL)

    Responsibilities:
    - playback lifecycle ownership
    - queue progression
    - event handling (NO bot.py involvement)
    - UI sync trigger
    """

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}
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
    # IDLE HANDLING
    # =====================================================
    def _cancel_idle(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        await asyncio.sleep(self.IDLE_TIMEOUT)

        state = music_manager.get_player(self._guild_id(player))

        if state.current or state.queue.all():
            return

        try:
            await player.disconnect()
        except Exception:
            pass

    # =====================================================
    # UI SYNC
    # =====================================================
    async def _notify_ui(self, player: wavelink.Player):
        try:
            guild = player.guild
            if not guild:
                return

            state = music_manager.get_player(guild.id)

            if not state.player_channel_id:
                return

            channel = guild.get_channel(state.player_channel_id)
            if not channel:
                return

            await player_message_manager.update(guild)

        except Exception as e:
            print(f"[MUSIC] UI update failed: {e}")

    # =====================================================
    # PLAYER REGISTRATION (STAGE 3.5 CORE)
    # =====================================================
    def bind_player(self, player: wavelink.Player):
        """
        Engine becomes owner of Lavalink events.
        """

        @player.on("track_end")
        async def _track_end(_):
            await self._play_next(player)

        @player.on("track_stuck")
        async def _track_stuck(_):
            await self._play_next(player)

        @player.on("track_exception")
        async def _track_exception(_):
            await self._play_next(player)

    # =====================================================
    # PLAYBACK CORE
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                await self._notify_ui(player)
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

                await self._notify_ui(player)

            except Exception as e:
                print(f"[MUSIC] play_next failed: {e}")
                state.current = None
                await self._play_next(player)

    # =====================================================
    # PUBLIC API
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        state.queue.add(track)

        self._cancel_idle(guild_id)

    async def start(self, player: wavelink.Player):
        state = music_manager.get_player(self._guild_id(player))

        if not state.current:
            await self._play_next(player)

    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        self._skip_guard.add(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        await self._play_next(player)

    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

        await self._notify_ui(player)


engine = MusicEngine()