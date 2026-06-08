import discord


class MusicPlayerView(discord.ui.View):
    """
    Persistent music control panel.

    Buttons:
    - pause/resume
    - skip
    - shuffle toggle
    - autoplay toggle (placeholder)
    """

    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    # -------------------------
    # PAUSE / RESUME
    # -------------------------

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.manager.get_player(self.guild_id)

        if player.is_playing:
            player.is_playing = False
            await interaction.response.send_message("⏸ Paused", ephemeral=True)
        else:
            player.is_playing = True
            await interaction.response.send_message("▶ Resumed", ephemeral=True)

    # -------------------------
    # SKIP
    # -------------------------

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.manager.get_player(self.guild_id)
        await player.skip()

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # -------------------------
    # SHUFFLE (stub)
    # -------------------------

    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.manager.get_player(self.guild_id)
        player.queue._queue = type(player.queue._queue)(list(player.queue._queue)[::-1])

        await interaction.response.send_message("🔀 Shuffled", ephemeral=True)