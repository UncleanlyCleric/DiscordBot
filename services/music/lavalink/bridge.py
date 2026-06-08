import discord
import wavelink

from services.music.models import Track


class VoiceBridge:

    async def connect(self, guild: discord.Guild, channel: discord.VoiceChannel):

        if not wavelink.Pool.nodes:
            raise RuntimeError("Lavalink not ready")

        vc = guild.voice_client

        if vc and isinstance(vc, wavelink.Player):
            if vc.channel != channel:
                await vc.move_to(channel)
            return vc

        # IMPORTANT: force Wavelink Player
        return await channel.connect(cls=wavelink.Player, self_deaf=True)

    async def play(self, player: wavelink.Player, track: Track) -> bool:

        if not player or not isinstance(player, wavelink.Player):
            print("[VOICE] Invalid player type")
            return False

        results = await wavelink.Playable.search(track.uri)

        if not results:
            print("[VOICE] No results")
            return False

        playable = results[0]

        await player.play(playable)

        print(f"[VOICE] Playing: {track.title}")

        return True


voice_bridge = VoiceBridge()