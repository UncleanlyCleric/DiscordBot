import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine
from services.music.player_message_manager import player_message_manager

from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # PLAYER GET (CLEAN - NO ENGINE BINDING)
    # =====================================================
    async def _get_player(self, interaction: discord.Interaction):

        if not interaction.guild:
            raise RuntimeError("Guild only command")

        voice_state = interaction.user.voice

        if not voice_state or not voice_state.channel:
            return None

        channel = voice_state.channel

        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            player = await channel.connect(cls=wavelink.Player)

        return player

    # =====================================================
    # PLAY
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

        primary = tracks[0]

        # =====================================================
        # ENGINE QUEUE FLOW
        # =====================================================
        await engine.enqueue(player, primary)

        state = music_manager.get_player(interaction.guild_id)

        for t in tracks[1:3]:
            state.queue.add(t)

        # START ONLY IF NEEDED
        await engine.start(player)

        # =====================================================
        # UI BOOTSTRAP (FIXED + SAFE)
        # =====================================================
        state = music_manager.get_player(interaction.guild_id)

        if not state.player_message_id and interaction.channel:

            msg = await interaction.channel.send(
                embed=build_now_playing_embed(state),
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = interaction.channel.id

        else:
            await player_message_manager.update(interaction.guild)

        await interaction.followup.send(
            content=f"🎵 Queued: **{primary.title}**"
        )

    # =====================================================
    # STOP
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
    # SKIP
    # =====================================================
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            await engine.skip(player)

        await player_message_manager.update(interaction.guild)

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # =====================================================
    # PAUSE
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
    # RESUME
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
    # QUEUE
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


# =====================================================
# EXTENSION ENTRYPOINT
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))