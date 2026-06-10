import discord
from discord import app_commands
from discord.ext import commands

import wavelink
import logging

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine


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
            player = await voice.channel.connect(
                cls=wavelink.Player
            )

        return player

    # =====================================================
    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        player = await self._get_player(interaction)

        if not player:
            return await interaction.followup.send(
                "Join a voice channel first."
            )

        state = music_manager.get_player(
            interaction.guild_id
        )

        state.player_channel_id = interaction.channel.id

        tracks = await music_resolver.resolve(
            query,
            interaction.user.id
        )

        if not tracks:
            return await interaction.followup.send(
                "No results."
            )

        for track in tracks:
            await engine.enqueue(player, track)

        await engine.start(player)

        await interaction.followup.send(
            f"🎵 Queued: **{tracks[0].title}** (+{len(tracks)-1})"
        )

    # =====================================================
    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            await engine.stop(player)

        await interaction.followup.send(
            "🛑 Stopped"
        )

    # =====================================================
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            await engine.skip(player)

        await interaction.followup.send(
            "⏭ Skipped"
        )

    # =====================================================
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(True)
            except Exception:
                pass

        await interaction.followup.send(
            "⏸ Paused"
        )

    # =====================================================
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(False)
            except Exception:
                pass

        await interaction.followup.send(
            "▶ Resumed"
        )

    # =====================================================
    @app_commands.command(name="queue")
    async def queue(self, interaction: discord.Interaction):

        state = music_manager.get_player(
            interaction.guild_id
        )

        tracks = state.queue.all()

        if not tracks:
            return await interaction.response.send_message(
                "Queue empty."
            )

        msg = "\n".join(
            f"{i+1}. {t.title}"
            for i, t in enumerate(tracks[:10])
        )

        await interaction.response.send_message(
            msg
        )

    # =====================================================
    # DEBUG PLAYER
    # =====================================================
    @app_commands.command(name="debugplayer")
    async def debugplayer(
        self,
        interaction: discord.Interaction
    ):

        player = interaction.guild.voice_client

        if not player:
            return await interaction.response.send_message(
                "No player"
            )

        await interaction.response.send_message(
            f"""
playing={player.playing}
paused={player.paused}
position={player.position}
connected={player.connected}
"""
        )

    # =====================================================
    # TRACK START
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload):

        logging.warning(
            "[TRACK_START] %s",
            getattr(
                payload.track,
                "title",
                "unknown"
            )
        )

    # =====================================================
    # TRACK END
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):

        logging.warning(
            "[TRACK_END] reason=%s",
            getattr(payload, "reason", None)
        )

        try:
            await engine.handle_track_end(
                payload.player
            )

        except Exception:
            logging.exception(
                "[TRACK_END] failed"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))