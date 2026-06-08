import discord
import wavelink

from services.music.models import Track


class VoiceBridge:
    """
    Real audio bridge using Wavelink player.
    """

    async def connect(self, guild: discord.Guild, channel: discord.VoiceChannel):
        player: wavelink.Player = guild.voice_client

        if player and player.is_connected():
            return player

        return await channel.connect(cls=wavelink.Player)

    async def play(self, guild_id: int, track: Track):
        guild = discord.utils.get(wavelink.Pool._bot.guilds, id=guild_id)
        if not guild:
            return

        player: wavelink.Player = guild.voice_client
        if not player:
            return

        # resolve track via Lavalink
        results = await wavelink.Playable.search(track.uri)

        if not results:
            return

        playable = results[0]

        await player.play(playable)


voice_bridge = VoiceBridge()