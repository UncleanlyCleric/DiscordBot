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

    # ---------------- PLAY / PAUSE ----------------
    @discord.ui.button(emoji="⏯", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        paused = gm.player.paused
        await gm.player.pause(not paused)

        await interaction.response.defer()

    # ---------------- SKIP ----------------
    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        if gm.player:
            await gm.player.stop()

        await interaction.response.defer()

    # ---------------- SHUFFLE ----------------
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        count = await gm.shuffle()

        await interaction.response.send_message(
            f"Shuffled {count} tracks.",
            ephemeral=True
        )

    # ---------------- STOP ----------------
    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        gm = self.gm()

        await gm.stop()

        await interaction.response.defer()