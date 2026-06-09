import asyncio

from services.music.manager import music_manager


class VoiceController:
    """
    Handles:
    - idle detection
    - auto disconnect
    """

    def __init__(self):
        self._tasks = {}

    async def monitor(self, player):
        guild_id = player.guild.id

        while True:
            state = music_manager.get_player(guild_id)

            # idle condition
            if not player.playing and not state.queue.all():
                await asyncio.sleep(10)

                # re-check
                if not player.playing and not state.queue.all():
                    try:
                        await player.disconnect()
                    except Exception:
                        pass
                    return

            await asyncio.sleep(5)

    def start(self, player):
        guild_id = player.guild.id

        if guild_id in self._tasks:
            return

        self._tasks[guild_id] = asyncio.create_task(self.monitor(player))


voice_controller = VoiceController()