import wavelink
from services.music.manager import music_manager


class PlayerEngine:

    async def play_next(self, guild):

        player: wavelink.Player = guild.voice_client

        if not player:
            return

        state = music_manager.get_player(guild.id)

        next_track = state.queue.next()

        if not next_track:
            state.current = None
            return

        state.current = next_track
        await player.play(next_track.playable)

    async def stop(self, guild):

        player: wavelink.Player = guild.voice_client

        if player:
            await player.stop()
            await player.disconnect()

        state = music_manager.get_player(guild.id)
        state.queue.clear()
        state.current = None


engine = PlayerEngine()