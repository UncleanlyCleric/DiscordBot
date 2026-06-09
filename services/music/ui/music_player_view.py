import discord
from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # SAFE STATE RESOLVE
    # =====================================================
    def _state(self, guild_id: int):
        return music_manager.get_player(guild_id)

    def _refresh_embed(self, guild_id: int):
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

        player = interaction.guild.voice_client if interaction.guild else None

        if player:
            try:
                await player.pause(not player.paused)
            except Exception:
                pass

        embed = self._refresh_embed(interaction.guild.id)

        await interaction.response.edit_message(embed=embed, view=self)

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip"
    )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        player = interaction.guild.voice_client if interaction.guild else None

        if player:
            from services.music.player_engine import engine
            await engine.skip(player)

        embed = self._refresh_embed(interaction.guild.id)

        await interaction.response.edit_message(embed=embed, view=self)

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        player = interaction.guild.voice_client if interaction.guild else None

        if player:
            from services.music.player_engine import engine
            await engine.stop(player)

        embed = self._refresh_embed(interaction.guild.id)

        await interaction.response.edit_message(embed=embed, view=self)