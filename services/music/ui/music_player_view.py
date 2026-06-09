import discord

from services.music.player_engine import engine


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # PAUSE / RESUME
    # =====================================================
    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.secondary,
        custom_id="music_pause_resume"
    )
    async def pause_resume(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.guild:
            return

        player = interaction.guild.voice_client
        if not player:
            return await interaction.response.defer()

        try:
            # keep engine unaware change minimal, but consistent
            if player.paused:
                await player.pause(False)
            else:
                await player.pause(True)
        except Exception:
            pass

        await interaction.response.defer()

    # =====================================================
    # SKIP (FIXED)
    # =====================================================
    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip"
    )
    async def skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.guild:
            return

        player = interaction.guild.voice_client
        if player:
            await engine.skip(player)

        await interaction.response.defer()

    # =====================================================
    # STOP (FIXED)
    # =====================================================
    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop"
    )
    async def stop(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.guild:
            return

        player = interaction.guild.voice_client
        if player:
            await engine.stop(player)

        await interaction.response.defer()