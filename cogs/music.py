import discord
from discord.ext import commands
from discord import app_commands

from music.manager import music_manager
from music.guild_music import create_guild_music_controller
from music.resolver import resolver
from ui.player import MusicPlayerView


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.controllers = {}

    def controller(self, guild_id: int):
        if guild_id not in self.controllers:
            self.controllers[guild_id] = create_guild_music_controller(
                self.bot,
                music_manager
            )
        return self.controllers[guild_id]

    # ---------------------------
    # /play
    # ---------------------------

    @app_commands.command(
        name="play",
        description="Play a song from YouTube, Spotify, etc."
    )
    async def play(
        self,
        interaction: discord.Interaction,
        query: str
    ):
        if not interaction.user.voice:
            await interaction.response.send_message(
                "Join a voice channel first.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        controller = self.controller(interaction.guild.id)

        track = await resolver.resolve(query)

        if not track:
            await interaction.followup.send(
                "Could not resolve track."
            )
            return

        vc = interaction.guild.voice_client

        if not vc:
            vc = await controller.connect(
                interaction.user.voice.channel
            )

        music_manager.add_to_queue(
            interaction.guild.id,
            track
        )

        if not vc.is_playing():
            await controller.play_next(
                interaction.guild.id,
                vc
            )

        embed = discord.Embed(
            title="Now Queued",
            description=track["title"],
            color=discord.Color.blurple()
        )

        view = MusicPlayerView(
            controller,
            interaction.guild.id
        )

        await interaction.followup.send(
            embed=embed,
            view=view
        )

    # ---------------------------
    # /skip
    # ---------------------------

    @app_commands.command(
        name="skip",
        description="Skip the current song."
    )
    async def skip(
        self,
        interaction: discord.Interaction
    ):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_playing():
            await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )
            return

        vc.stop()

        await interaction.response.send_message(
            "Skipped."
        )

    # ---------------------------
    # /queue
    # ---------------------------

    @app_commands.command(
        name="queue",
        description="Show the current queue."
    )
    async def queue(
        self,
        interaction: discord.Interaction
    ):
        queue = music_manager.get_queue(
            interaction.guild.id
        )

        if not queue:
            await interaction.response.send_message(
                "Queue is empty.",
                ephemeral=True
            )
            return

        msg = "\n".join(
            f"{i+1}. {t['title']}"
            for i, t in enumerate(queue)
        )

        await interaction.response.send_message(
            f"**Queue:**\n{msg}"
        )


async def setup(bot):
    await bot.add_cog(MusicCog(bot))