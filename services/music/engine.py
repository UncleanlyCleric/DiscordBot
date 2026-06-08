import wavelink
from services.music.queue_manager import queue_manager


class PlaybackEngine:

    async def play_next(self, guild):

        player: wavelink.Player = guild.voice_client
        if not player:
            return

        track = queue_manager.next(guild.id)

        if not track:
            queue_manager.set_current(guild.id, None)
            return

        queue_manager.set_current(guild.id, track)

        await player.play(track.playable)

    async def stop(self, guild):

        player: wavelink.Player = guild.voice_client

        if player:
            await player.stop()
            await player.disconnect()

        queue_manager.clear(guild.id)


engine = PlaybackEngine()