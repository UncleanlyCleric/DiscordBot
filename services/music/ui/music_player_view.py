import logging
import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # SAFE STATE (ONLY USE GUILD ID)
    # =====================================================
    def _state(self, guild_id: int):
        return music_manager.get_player(guild_id)

    def _embed(self, guild_id: int):
        state = self._state(guild_id)
        return build_now_playing_embed(state)

    # =====================================================
    # PAUSE / RESUME
    # =====================================================
    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.secondary,
        custom_id="music_pause_resume"
    )
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):

        logging.info("[UI] pause_resume")

        try:
            player = interaction.guild.voice_client

            if player:
                await player.pause(not player.paused)

            await interaction.response.edit_message(
                embed=self._embed(interaction.guild.id),
                view=self
            )

        except Exception:
            logging.exception("[UI] pause_resume failed")

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip"
    )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        logging.info("[UI] skip")

        try:
            player = interaction.guild.voice_client

            if player:
                from services.music.player_engine import engine
                await engine.skip(player)

            await interaction.response.edit_message(
                embed=self._embed(interaction.guild.id),
                view=self
            )

        except Exception:
            logging.exception("[UI] skip failed")

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        logging.info("[UI] stop")

        try:
            player = interaction.guild.voice_client

            if player:
                from services.music.player_engine import engine
                await engine.stop(player)

                try:
                    await player.disconnect()
                except Exception:
                    pass

            await interaction.response.edit_message(
                embed=self._embed(interaction.guild.id),
                view=self
            )

        except Exception:
            logging.exception("[UI] stop failed")