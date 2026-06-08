import discord
import wavelink

from services.music.models import Track


class VoiceBridge:
    """
    ONLY handles voice connection.
    NO PLAYBACK LOGIC HERE.
    """

    async def connect(self, guild: discord.Guild, channel: discord.VoiceChannel):
        if not wavelink.Pool.nodes:
            raise RuntimeError("Lavalink not ready")

        if guild.voice_client:
            if guild.voice_client.channel != channel:
                await guild.voice_client.move_to(channel)
            return guild.voice_client

        return await channel.connect(cls=wavelink.Player)

    async def play(self, *args, **kwargs):
        raise RuntimeError(
            "VoiceBridge.play is disabled. Playback is handled by MusicController."
        )


voice_bridge = VoiceBridge()