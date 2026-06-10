import discord
from discord import app_commands
from discord.ext import commands
import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine
from services.music.player_message_manager import player_message_manager


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    async def _get_player(self, interaction: discord.Interaction):

        if not interaction.guild:
            return None

        voice = interaction.user.voice

        if not voice or not voice.channel:
            return None

        player = interaction.guild.voice_client

        if not player:
            player = await voice.channel.connect(cls=wavelink.Player)

        return player

    # =====================================================
    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        player = await self._get_player(interaction)

        if not player:
            return await interaction.followup.send("Join a voice channel first.")

        tracks = await music_resolver.resolve(query, interaction.user.id)

        if not tracks:
            return await interaction.followup.send("No results.")

        # =====================================================
        # ENQUEUE ALL TRACKS
        # =====================================================
        for t in tracks:
            await engine.enqueue(player, t)

        # =====================================================
        # START ONLY IF NOT PLAYING
        # =====================================================
        if not player.playing:
            await engine.start(player)

        # =====================================================
        # UI INIT (ONLY ONCE)
        # =====================================================
        state = music_manager.get_player(interaction.guild_id)
        state.player_channel_id = interaction.channel.id

        await player_message_manager.update(interaction.guild)

        await interaction.followup.send(
            f"🎵 Queued: **{tracks[0].title}** (+{len(tracks)-1})"
        )

    # =====================================================
    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            await engine.stop(player)
            try:
                await player.disconnect()
            except Exception:
                pass

        await player_message_manager.update(interaction.guild)

        await interaction.response.send_message("🛑 Stopped", ephemeral=True)

    # =====================================================
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            await engine.skip(player)

        await player_message_manager.update(interaction.guild)

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # =====================================================
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(True)
            except Exception:
                pass

        await player_message_manager.update(interaction.guild)

        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    # =====================================================
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(False)
            except Exception:
                pass

        await player_message_manager.update(interaction.guild)

        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    # =====================================================
    @app_commands.command(name="queue")
    async def queue(self, interaction: discord.Interaction):

        state = music_manager.get_player(interaction.guild_id)

        tracks = state.queue.all()

        if not tracks:
            return await interaction.response.send_message("Queue empty.")

        msg = "\n".join(
            f"{i + 1}. {t.title}"
            for i, t in enumerate(tracks[:10])
        )

        await interaction.response.send_message(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))