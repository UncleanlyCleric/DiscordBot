import discord
import wavelink

from services.music.models import Track


class VoiceBridge:
    """
    Wavelink/Lavalink bridge.
    """

    async def connect(
        self,
        guild: discord.Guild,
        channel: discord.VoiceChannel,
    ):
        if not wavelink.Pool.nodes:
            raise RuntimeError(
                "Lavalink is not ready (no active nodes)"
            )

        voice_client = guild.voice_client

        if voice_client:
            if voice_client.channel != channel:
                await voice_client.move_to(channel)

            return voice_client

        return await channel.connect(
            cls=wavelink.Player
        )

    async def play(
        self,
        guild: discord.Guild,
        track: Track,
    ) -> bool:
        player: wavelink.Player = guild.voice_client

        if not player:
            return False

        results = await wavelink.Playable.search(
            track.uri
        )

        if not results:
            return False

        playable = results[0]

        await player.play(playable)

        return True


voice_bridge = VoiceBridge()