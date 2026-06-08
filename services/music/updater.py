import discord
import asyncio

from services.music.manager import music_manager


class NowPlayingUpdater:
    """
    Periodically updates Now Playing messages (future enhancement hook).
    """

    def __init__(self):
        self.tasks = {}

    async def start(self, bot: discord.Client, guild_id: int, channel_id: int):
        if guild_id in self.tasks:
            return

        async def loop():
            channel = bot.get_channel(channel_id)

            if not channel:
                return

            while True:
                player = music_manager.get_player(guild_id)

                if not player.current:
                    await asyncio.sleep(5)
                    continue

                embed = discord.Embed(
                    title="🎧 Now Playing",
                    description=player.current.title,
                    color=discord.Color.green()
                )

                try:
                    await channel.send(embed=embed)
                except:
                    pass

                await asyncio.sleep(30)

        self.tasks[guild_id] = asyncio.create_task(loop())

    def stop(self, guild_id: int):
        task = self.tasks.get(guild_id)

        if task:
            task.cancel()
            del self.tasks[guild_id]


now_playing_updater = NowPlayingUpdater()