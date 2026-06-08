from typing import Dict

from services.music.controller import music_controller
from services.music.manager import music_manager


class MusicRuntime:
    """
    Responsible for starting/stopping playback loops
    per guild automatically.
    """

    def __init__(self):
        self.active_loops: Dict[int, bool] = {}

    async def start_guild(self, guild_id: int):
        """
        Start playback loop for a guild if not already running.
        """

        if self.active_loops.get(guild_id):
            return

        self.active_loops[guild_id] = True
        await music_controller.start_loop(guild_id)

    def stop_guild(self, guild_id: int):
        """
        Stop playback loop.
        """

        self.active_loops[guild_id] = False
        music_controller.stop_loop(guild_id)

    async def restart_all(self):
        """
        Called on bot startup to restore playback sessions.
        """

        for player in music_manager.get_all():
            if player.is_playing or len(player.queue) > 0:
                await self.start_guild(player.guild_id)


music_runtime = MusicRuntime()