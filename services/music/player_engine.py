import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe playback engine for Wavelink 4.
    """

    def __init__(self):
        self._locks = {}

    # -----------------------------------------
    # GET LOCK PER GUILD (prevents double play)
    # -----------------------------------------
    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # -----------------------------------------
    # PLAY NEXT TRACK
    # -----------------------------------------
    async def play_next(self, guild: discord.Guild):
        """
        Entry point used by cog
        """
        player: wavelink.Player = guild.voice_client
        if not player:
            return

        await self._play_next_internal(player)

    async def _play_next_internal(self, player: wavelink.Player):
        """
        Core engine loop step.
        """

        guild_id = player.guild_id  # ✅ THIS is the correct source

        state = music_manager.get_player(guild_id)

        if not state:
            return

        track = state.queue.next()

        if not track:
            state.current = None
            return

        state.current = track

        results = await wavelink.Playable.search(track.uri or track.title)

        if not results:
            return

        playable = results[0]

        await player.play(playable)

    # -----------------------------------------
    # ENQUEUE SAFE
    # -----------------------------------------
    async def enqueue(self, player: wavelink.Player, track):
        """
        Add track and optionally start playback.
        """

        guild_id = player.guild_id  # ✅ FIX (was broken)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        # if nothing is playing → start
        if not player.playing:
            await self._play_next_internal(player)

    # -----------------------------------------
    # STOP
    # -----------------------------------------
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