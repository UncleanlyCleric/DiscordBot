import discord


class PlayerView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    def gm(self):
        return self.bot.get_cog("Music").get_player(self.guild_id)

    # =====================================================
    # ROW 1 - PLAYBACK
    # =====================================================

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        prev = await gm.play_previous()

        if not prev:
            return await interaction.response.send_message(
                "No previous track.",
                ephemeral=True
            )

        await interaction.response.defer()

    @discord.ui.button(emoji="⏯", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        await gm.player.pause(not gm.player.paused)
        await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        gm.skip_lock = True
        await gm.player.stop()
        gm.skip_lock = False

        await interaction.response.defer()

    # =====================================================
    # ROW 2 - QUEUE CONTROL
    # =====================================================

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        count = await gm.shuffle()

        await interaction.response.send_message(
            f"Shuffled {count} tracks.",
            ephemeral=True
        )

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        gm.radio_enabled = not gm.radio_enabled

        await interaction.response.send_message(
            f"Repeat: {'ON' if gm.radio_enabled else 'OFF'}",
            ephemeral=True
        )

    # (placeholder for future queue view button)
    # @discord.ui.button(emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    # async def queue(self, interaction, button):
    #     ...

    # =====================================================
    # ROW 3 - AUDIO CONTROL
    # =====================================================

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=2)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        await gm.set_volume(gm.volume - 10)

        await interaction.response.send_message(
            f"Volume: {gm.volume}",
            ephemeral=True
        )

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=2)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        await gm.set_volume(gm.volume + 10)

        await interaction.response.send_message(
            f"Volume: {gm.volume}",
            ephemeral=True
        )

    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.danger, row=2)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        await gm.stop()
        await interaction.response.defer()