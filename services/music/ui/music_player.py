import discord

from services.music.engine import engine
from services.music.manager import music_manager


class MusicPlayerView(discord.ui.View):

    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    # =====================================================
    # PAUSE
    # =====================================================
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.pause(True)

        await interaction.response.defer()

    # =====================================================
    # RESUME
    # =====================================================
    @discord.ui.button(label="Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.pause(False)

        await interaction.response.defer()

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.stop()

        await interaction.response.defer()

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()

        state = music_manager.get_player(self.guild_id)
        state.queue.clear()
        state.current = None

        await interaction.response.defer()

    # =====================================================
    # SHUFFLE
    # =====================================================
    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client

        if vc:
            await engine.shuffle(vc)

        await interaction.response.defer()

    # =====================================================
    # VOLUME DOWN
    # =====================================================
    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.gray)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            gid = interaction.guild.id

            current = engine.get_volume(gid)
            engine.set_volume(gid, current - 10)

            try:
                await vc.set_volume(engine.get_volume(gid))
            except Exception:
                pass

        await interaction.response.defer()

    # =====================================================
    # VOLUME UP
    # =====================================================
    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.gray)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            gid = interaction.guild.id

            current = engine.get_volume(gid)
            engine.set_volume(gid, current + 10)

            try:
                await vc.set_volume(engine.get_volume(gid))
            except Exception:
                pass

        await interaction.response.defer()