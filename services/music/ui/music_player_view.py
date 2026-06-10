import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    def _state(self, guild_id: int):
        return music_manager.get_player(guild_id)

    def _refresh_embed(self, guild_id: int):
        state = self._state(guild_id)
        return build_now_playing_embed(state)

    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.secondary,
        custom_id="music_pause_resume"
    )
    async def pause_resume(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(not player.paused)
            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip"
    )
    async def skip(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.skip(player)

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.stop(player)

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )