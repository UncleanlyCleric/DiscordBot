import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    SINGLE SOURCE OF TRUTH FOR PLAYBACK

    Rules:
    - ONLY this file pops queue
    - ONLY this file advances tracks
    - Wavelink events are dumb triggers
    """

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
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

        raise RuntimeError("Cannot resolve guild id")

    # =====================================================
    # LOCK
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        if not state.current:
            await self._play_next(player)

    # =====================================================
    # PLAY NEXT (CORE)
    # =====================================================
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            # =================================================
            # SKIP GUARD (PREVENT DOUBLE ADVANCE)
            # =================================================
            if self._skip_lock.pop(guild_id, False):
                return

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                return

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

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        # prevent double advance from track_end firing right after skip
        self._skip_lock[guild_id] = True

        state = music_manager.get_player(guild_id)

        # clear current track immediately
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

    # =====================================================
    # IMPORTANT FIX:
    # explicitly advance queue AFTER stop
    # =====================================================
    await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()