import asyncio
import discord
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 engine.
    No assumptions about guild_id availability.
    """

    def __init__(self):
        self._locks = {}

    # =====================================================
    # SAFE GUILD ID RESOLUTION
    # =====================================================
    def _get_guild_id(self, player: wavelink.Player) -> int:
        """
        Works across ALL Wavelink versions safely.
        """

        guild = getattr(player, "guild", None)
        if guild:
            return guild.id

        # fallback 1: discord attribute
        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        # fallback 2: last resort
        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # LOCK
    # =====================================================
    def _lock(self, guild_id: int):
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        guild_id = self._get_guild_id(player)  # ✅ FIX

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        if not player.playing:
            await self._play_next(player)

    # =====================================================
    # PLAY NEXT
    # =====================================================
    async def play_next(self, guild: discord.Guild):

        player: wavelink.Player = guild.voice_client
        if not player:
            return

        await self._play_next(player)

    # =====================================================
    # CORE PLAYBACK
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        guild_id = self._get_guild_id(player)

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
    # STOP
    # =====================================================
    async def stop(self, guild: discord.Guild):

        player: wavelink.Player = guild.voice_client

        if player:
            try:
                await player.stop()
            except Exception:
                pass

        state = music_manager.get_player(guild.id)
        state.current = None
        state.queue.clear()


engine = MusicEngine()