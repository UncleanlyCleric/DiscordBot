import discord


class PlayerView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    def gm(self):
        return self.bot.get_cog("Music").get_player(self.guild_id)

    # ---------------- BACK ----------------
    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        prev = await gm.play_previous()

        if not prev:
            return await interaction.response.send_message(
                "No previous track.",
                ephemeral=True
            )

        await interaction.response.defer()

    # ---------------- PLAY/PAUSE ----------------
    @discord.ui.button(emoji="⏯", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction, button):
        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        await gm.player.pause(not gm.player.paused)
        await interaction.response.defer()

    # ---------------- SKIP ----------------
    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction, button):
        gm = self.gm()

        gm.skip_lock = True
        await gm.player.stop()
        gm.skip_lock = False

        await interaction.response.defer()

    # ---------------- VOLUME DOWN ----------------
    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction, button):
        gm = self.gm()
        await gm.set_volume(gm.volume - 10)

        await interaction.response.send_message(
            f"Volume: {gm.volume}",
            ephemeral=True
        )

    # ---------------- VOLUME UP ----------------
    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction, button):
        gm = self.gm()
        await gm.set_volume(gm.volume + 10)

        await interaction.response.send_message(
            f"Volume: {gm.volume}",
            ephemeral=True
        )

    # ---------------- SHUFFLE ----------------
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction, button):
        gm = self.gm()

        count = await gm.shuffle()

        await interaction.response.send_message(
            f"Shuffled {count} tracks.",
            ephemeral=True
        )

    # ---------------- STOP ----------------
    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction, button):
        gm = self.gm()

        await gm.stop()
        await interaction.response.defer()