import discord
import wavelink

from services.music.models import Track


class VoiceBridge:

    async def connect(self, guild: discord.Guild, channel: discord.VoiceChannel):
        if not wavelink.Pool.nodes:
            raise RuntimeError("Lavalink is not ready")

        if guild.voice_client:
            if guild.voice_client.channel != channel:
                await guild.voice_client.move_to(channel)
            return guild.voice_client

        return await channel.connect(cls=wavelink.Player)

    async def play(self, guild: discord.Guild, track: Track) -> bool:
        player: wavelink.Player = guild.voice_client

        if not player:
            return False

        # 🚨 KEY FIX: DO NOT re-search here
        # The resolver ALREADY decided what this is
        query = track.uri

        try:
            # Let wavelink fully resolve properly
            results = await wavelink.Playable.search(query)
        except Exception as e:
            print(f"[VoiceBridge] search error: {e}")
            return False

        if not results:
            return False

        playable = results[0]

        # 🚨 CRITICAL FIX: ensure proper encoding exists
        if not getattr(playable, "encoded", None):
            try:
                playable = await wavelink.Playable.search(f"ytsearch:{track.title}")
                playable = playable[0] if playable else None
            except Exception:
                return False

        if not playable:
            return False

        try:
            # 🚨 IMPORTANT: stop current before playing new track
            if player.playing or player.paused:
                await player.stop()

            await player.play(playable)

            return True

        except Exception as e:
            print(f"[VoiceBridge] play failed: {e}")
            return False


voice_bridge = VoiceBridge()