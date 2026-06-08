import asyncio
import discord  # ✅ FIX: required for type hints
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe playback engine for Wavelink 4.
    """

    def __init__(self):
        self._locks = {}

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # ENTRY POINT
    # =====================================================
    async def play_next(self, guild: discord.Guild):
        player: wavelink.Player = guild.voice_client
        if not player:
            return

        await self._play_next_internal(player)

    # =====================================================
    # INTERNAL PLAY
    # =====================================================
    async def _play_next_internal(self, player: wavelink.Player):

        guild_id = player.guild_id  # IMPORTANT FIX

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
            await self._play_next_internal(player)

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        state = music_manager.get_player(player.guild_id)

        state.queue.add(track)

        if not player.playing:
            await self._play_next_internal(player)

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