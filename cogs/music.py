import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # INTERNAL
    # =====================================================
    def get_player(self, guild: discord.Guild) -> wavelink.Player:
        vc = guild.voice_client
        return vc if isinstance(vc, wavelink.Player) else None

    # =====================================================
    # PLAY
    # =====================================================
    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send("Join a voice channel.")

        channel = interaction.user.voice.channel
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            player = await channel.connect(cls=wavelink.Player)

        tracks = await music_resolver.resolve(query, interaction.user.id)

        if not tracks:
            return await interaction.followup.send("No results.")

        state = music_manager.get_player(interaction.guild_id)
        state.queue.add_many(tracks)

        # 🚀 SINGLE SOURCE OF TRUTH
        await engine.ensure_playing(interaction.guild)

        await interaction.followup.send(
            f"Queued: {tracks[0].title}"
        )

    # =====================================================
    # STOP
    # =====================================================
    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):

        await engine.stop(interaction.guild)

        await interaction.response.send_message("Stopped.", ephemeral=True)

    # =====================================================
    # PAUSE (Wavelink 4 correct)
    # =====================================================
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):

        player = self.get_player(interaction.guild)

        if not player:
            return await interaction.response.send_message(
                "Nothing playing.",
                ephemeral=True
            )

        await player.pause(True)

        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    # =====================================================
    # RESUME (Wavelink 4 correct)
    # =====================================================
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):

        player = self.get_player(interaction.guild)

        if not player:
            return await interaction.response.send_message(
                "Nothing playing.",
                ephemeral=True
            )

        await player.pause(False)

        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    # =====================================================
    # SKIP
    # =====================================================
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        player = self.get_player(interaction.guild)

        if player:
            await player.stop()

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # =====================================================
    # QUEUE
    # =====================================================
    @app_commands.command(name="queue")
    async def queue(self, interaction: discord.Interaction):

        state = music_manager.get_player(interaction.guild_id)
        tracks = state.queue.all()

        if not tracks:
            return await interaction.response.send_message("Queue empty.")

        msg = "\n".join(
            f"{i+1}. {t.title}" for i, t in enumerate(tracks[:10])
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎶 Queue",
                description=msg
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))