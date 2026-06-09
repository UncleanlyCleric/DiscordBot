import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 music engine.

    Contract:
        ALL methods accept wavelink.Player ONLY.
        No discord.Guild usage anywhere in public API.
    """

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}

    # =====================================================
    # INTERNAL: RESOLVE GUILD ID SAFELY
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        # fallback for edge builds / wrappers
        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # INTERNAL LOCK (prevents race conditions)
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # ENQUEUE TRACK
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        """
        Add track to queue and start playback if idle.
        """

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        # start playback if idle
        if not player.playing:
            await self._play_next(player)

    # =====================================================
    # PLAY NEXT (PUBLIC SAFE ENTRY)
    # =====================================================
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    # =====================================================
    # CORE PLAYBACK ENGINE
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        """
        Pull next track from queue and play it.
        """

        guild_id = self._guild_id(player)

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
    # SKIP TRACK
    # =====================================================
    async def skip(self, player: wavelink.Player):
        """
        Skip current track and immediately play next.
        """

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        state.current = None

        await self._play_next(player)

    # =====================================================
    # STOP FULL PLAYBACK
    # =====================================================
    async def stop(self, player: wavelink.Player):
        """
        Stop playback and clear queue/state.
        """

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass


# Singleton
engine = MusicEngine()