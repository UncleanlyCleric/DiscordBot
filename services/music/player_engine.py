import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 music engine.

    Responsibilities:
    - playback control only
    - queue consumption
    - concurrency safety
    """

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}

    # =====================================================
    # INTERNAL: GUILD ID RESOLUTION
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # LOCK PER GUILD (CRITICAL FIX)
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

        # -----------------------------
        # QUEUE INTELLIGENCE HOOK POINT
        # (dedupe should happen here or in queue class)
        # -----------------------------
        state.queue.add(track)

        if not player.playing:
            await self._play_next(player)

    # =====================================================
    # PUBLIC: PLAY NEXT
    # =====================================================
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    # =====================================================
    # CORE PLAYBACK ENGINE (LOCKED)
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                return

            state.current = track

            try:
                results = await wavelink.Playable.search(
                    track.uri or track.title
                )

                if not results:
                    return

                await player.play(results[0])

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        state.current = None

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