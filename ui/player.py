import discord


class MusicPlayerView(discord.ui.View):
    """
    SAFE UI VIEW

    RULES:
    - NO imports from music/
    - NO DB/storage access
    - NO business logic
    - ONLY button events + callbacks
    """

    def __init__(self, controller, guild_id: int):
        super().__init__(timeout=None)

        self.controller = controller
        self.guild_id = guild_id

    # ---------------------------
    # Controls
    # ---------------------------

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client

        if not vc:
            await interaction.response.send_message("Not connected.", ephemeral=True)
            return

        vc.stop()

        await interaction.response.send_message("Skipped track.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client

        if vc and vc.is_connected():
            await vc.disconnect()

        await interaction.response.send_message("Disconnected.", ephemeral=True)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue = self.controller.music.get_queue(self.guild_id)

        if not queue:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)
            return

        msg = "\n".join(
            f"{i+1}. {t['title']}" for i, t in enumerate(queue)
        )

        await interaction.response.send_message(f"**Queue:**\n{msg}", ephemeral=True)