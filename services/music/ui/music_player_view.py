import discord


def progress_bar(current: int, total: int, length: int = 12):
    if not total:
        return "▱" * length

    ratio = min(max(current / total, 0), 1)
    filled = int(ratio * length)

    return "▰" * filled + "▱" * (length - filled)


class MusicPlayerView(discord.ui.View):
    """
    Phase 11 UI Layer

    - DOES NOT control playback directly
    - ONLY calls bot/cog methods
    """

    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)

        self.bot = bot
        self.guild_id = guild_id

    # =====================================================
    # HELPERS
    # =====================================================
    def get_player_state(self):
        return self.bot.get_cog("MusicCog").get_state(self.guild_id)

    def get_engine(self):
        return self.bot.get_cog("MusicCog").engine

    # =====================================================
    # PLAY/PAUSE (optional future expand)
    # =====================================================
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.get_player_state()

        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            await vc.pause()
            button.label = "Resume"
        else:
            await vc.resume()
            button.label = "Pause"

        await interaction.response.edit_message(view=self)

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        engine = self.get_engine()
        vc = interaction.guild.voice_client

        if vc:
            await engine.skip(vc)

        await interaction.response.defer()

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        engine = self.get_engine()
        vc = interaction.guild.voice_client

        if vc:
            await engine.stop(vc)

        await interaction.response.defer()