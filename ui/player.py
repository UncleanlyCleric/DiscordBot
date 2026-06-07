import discord


class PlayerView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    # =====================================================
    # MUSIC COG ACCESS
    # =====================================================
    def gm(self):
        cog = self.bot.get_cog("Music")
        return cog.get_player(self.guild_id)

    # =====================================================
    # PLAY / PAUSE
    # =====================================================
    @discord.ui.button(label="⏯", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        if gm.player.paused:
            await gm.player.pause(False)
        else:
            await gm.player.pause(True)

        await interaction.response.defer()

    # =====================================================
    # SKIP
    # =====================================================
    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()

        await gm.skip()
        await interaction.response.defer()

    # =====================================================
    # SHUFFLE
    # =====================================================
    @discord.ui.button(label="🔀", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        count = await gm.shuffle()

        await interaction.response.send_message(
            f"🔀 Shuffled {count} tracks.",
            ephemeral=True
        )

    # =====================================================
    # AUTOPLAY / RADIO TOGGLE
    # =====================================================
    @discord.ui.button(label="🔁", style=discord.ButtonStyle.success)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        gm.radio_enabled = not gm.radio_enabled

        await interaction.response.send_message(
            f"Autoplay: {gm.radio_enabled}",
            ephemeral=True
        )

    # =====================================================
    # STOP
    # =====================================================
    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        await gm.stop()

        await interaction.response.defer()

    # =====================================================
    # VOLUME DOWN
    # =====================================================
    @discord.ui.button(label="➖", style=discord.ButtonStyle.secondary, row=1)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        await gm.volume_down()

        await interaction.response.defer()

    # =====================================================
    # VOLUME UP
    # =====================================================
    @discord.ui.button(label="➕", style=discord.ButtonStyle.secondary, row=1)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        await gm.volume_up()

        await interaction.response.defer()