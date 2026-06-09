import discord
import asyncio

from services.music.manager import music_manager
from services.music.engine import engine
from ui.music_player import MusicPlayerView


class MusicPlayerUI:
    """
    Persistent Spotify-style player UI per guild.
    """

    def __init__(self, bot):
        self.bot = bot
        self.messages: dict[int, discord.Message] = {}
        self.tasks: dict[int, asyncio.Task] = {}

    # =====================================================
    # START UI
    # =====================================================
    async def start(self, guild: discord.Guild):
        guild_id = guild.id

        if guild_id in self.tasks:
            return

        self.tasks[guild_id] = asyncio.create_task(self._loop(guild))

    # =====================================================
    # STOP UI
    # =====================================================
    async def stop(self, guild_id: int):
        task = self.tasks.get(guild_id)

        if task:
            task.cancel()

        self.tasks.pop(guild_id, None)
        self.messages.pop(guild_id, None)

    # =====================================================
    # MAIN LOOP
    # =====================================================
    async def _loop(self, guild: discord.Guild):

        guild_id = guild.id

        await self.bot.wait_until_ready()

        while True:
            try:
                state = music_manager.get_player(guild_id)

                vc = guild.voice_client
                channel = vc.channel if vc else None

                if not channel:
                    await asyncio.sleep(3)
                    continue

                embed = self._build_embed(state, guild_id)

                view = MusicPlayerView(self.bot, guild_id)

                msg = self.messages.get(guild_id)

                if msg:
                    await msg.edit(embed=embed, view=view)
                else:
                    self.messages[guild_id] = await channel.send(
                        embed=embed,
                        view=view
                    )

            except Exception as e:
                print(f"[UI] error: {e}")

            await asyncio.sleep(3)

    # =====================================================
    # EMBED
    # =====================================================
    def _build_embed(self, state, guild_id: int):

        embed = discord.Embed(
            title="🎧 Now Playing",
            color=discord.Color.blurple()
        )

        if state.current:
            embed.description = f"**{state.current.title}**"
        else:
            embed.description = "Nothing playing"

        queue = state.queue.all()[:5]

        if queue:
            embed.add_field(
                name="Up Next",
                value="\n".join(t.title for t in queue),
                inline=False
            )

        embed.add_field(
            name="Volume",
            value=f"{engine.get_volume(guild_id)}%",
            inline=True
        )

        return embed