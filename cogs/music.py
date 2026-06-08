import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_service import player_service


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -----------------------------
    # PLAY
    # -----------------------------
    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        state = music_manager.get_player(interaction.guild_id)

        if not interaction.user.voice:
            return await interaction.followup.send("Join a voice channel first.")

        channel = interaction.user.voice.channel

        player = await player_service.connect(interaction.guild, channel)

        tracks = await music_resolver.resolve(query, interaction.user.id)

        if not tracks:
            return await interaction.followup.send("No results found.")

        for t in tracks:
            state.queue.add(t)

        # start if idle
        if not player.playing:
            next_track = state.queue.next()
            state.current = next_track
            await player.play(next_track.playable)

        await interaction.followup.send(f"Queued: {tracks[0].title}")

    # -----------------------------
    # SKIP
    # -----------------------------
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        player: wavelink.Player = interaction.guild.voice_client

        if player:
            await player.stop()

        await interaction.response.send_message("Skipped", ephemeral=True)

    # -----------------------------
    # PAUSE
    # -----------------------------
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):

        player: wavelink.Player = interaction.guild.voice_client

        if player:
            await player.pause(True)

        await interaction.response.send_message("Paused", ephemeral=True)

    # -----------------------------
    # RESUME
    # -----------------------------
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):

        player: wavelink.Player = interaction.guild.voice_client

        if player:
            await player.pause(False)

        await interaction.response.send_message("Resumed", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))