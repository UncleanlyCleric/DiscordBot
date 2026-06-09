import discord
import logging

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    def _state(self, interaction: discord.Interaction):
        return music_manager.get_player(interaction.guild.id)

    def _refresh(self, interaction: discord.Interaction):
        return build_now_playing_embed(self._state(interaction))

    # =====================================================
    # PAUSE / RESUME
    # =====================================================
    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.secondary,
        custom_id="music_pause_resume"
    )
    async def pause_resume(self, interaction, button):

        if not interaction.guild:
            return

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(not player.paused)
            except Exception as e:
                logging.exception("[UI] pause failed: %s", e)

        await interaction.response.edit_message(
            embed=self._refresh(interaction),
            view=self
        )

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip"
    )
    async def skip(self, interaction, button):

        if not interaction.guild:
            return

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.skip(player)

        await interaction.response.edit_message(
            embed=self._refresh(interaction),
            view=self
        )

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(self, interaction, button):

        if not interaction.guild:
            return

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.stop(player)

        await interaction.response.edit_message(
            embed=self._refresh(interaction),
            view=self
        )