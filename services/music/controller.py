import wavelink
import asyncio

from services.music.manager import music_manager
from services.music.lavalink.bridge import voice_bridge


class MusicController:
    """
    Event-driven music controller.
    No polling loops.
    """

    def __init__(self):
        self.lock = asyncio.Lock()

    # =====================================================
    # CORE ENTRY POINT
    # =====================================================
    async def play_next(self, guild_id: int):

        async with self.lock:
            player = music_manager.get_player(guild_id)

            track = player.queue.next()

            if not track:
                player.current = None
                return

            player.current = track

            guild = self._get_guild(guild_id)
            if not guild:
                return

            vc = guild.voice_client
            if not vc:
                return

            try:
                await voice_bridge.play(guild, track)
            except Exception as e:
                print(f"[MusicController] play error: {e}")
                await self.play_next(guild_id)

    # =====================================================
    # TRACK END EVENT HOOK
    # =====================================================
    async def on_track_end(self, payload):

        player = payload.player
        if not player:
            return

        guild = getattr(player, "guild", None)
        if not guild:
            return

        guild_id = guild.id

        await self.play_next(guild_id)

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================
    def _get_guild(self, guild_id: int):
        for node in wavelink.Pool.nodes.values():
            bot = getattr(node, "_client", None)
            if bot:
                guild = bot.get_guild(guild_id)
                if guild:
                    return guild
        return None


music_controller = MusicController()