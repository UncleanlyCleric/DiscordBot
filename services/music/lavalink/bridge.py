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
            raise RuntimeError("Lavalink is not ready (no active nodes)")

        voice_client = guild.voice_client

        if voice_client:
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
            return voice_client

        return await channel.connect(cls=wavelink.Player)

    # =====================================================
    # FIXED PLAY LOGIC
    # =====================================================
    async def play(self, guild: discord.Guild, track: Track) -> bool:
        player: wavelink.Player = guild.voice_client

        if not player:
            return False

        query = track.uri

        # -------------------------------------------------
        # FIX 1: normalize search prefixes
        # -------------------------------------------------
        if not query.startswith(("http", "ytmsearch:", "scsearch:")):
            query = f"ytmsearch:{query}"

        # -------------------------------------------------
        # FIX 2: search Lavalink safely
        # -------------------------------------------------
        try:
            results = await wavelink.Playable.search(query)
        except Exception as e:
            print(f"[VoiceBridge] search failed: {e}")
            return False

        if not results:
            return False

        playable = results[0]

        # -------------------------------------------------
        # FIX 3: guard against null encoding (YOUR BUG)
        # -------------------------------------------------
        if not getattr(playable, "encoded", None) and not getattr(playable, "identifier", None):
            print("[VoiceBridge] invalid playable received")
            return False

        # -------------------------------------------------
        # FIX 4: play safely
        # -------------------------------------------------
        try:
            await player.play(playable)
        except Exception as e:
            print(f"[VoiceBridge] play failed: {e}")
            return False

        return True


voice_bridge = VoiceBridge()