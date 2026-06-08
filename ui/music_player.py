import discord
import wavelink


class MusicPlayerView(discord.ui.View):
    """
    Persistent music control panel.
    """

    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=None)

        self.cog = cog
        self.guild_id = guild_id

    # =====================================================
    # PAUSE / RESUME
    # =====================================================

    @discord.ui.button(
        label="Pause",
        style=discord.ButtonStyle.primary
    )
    async def pause_resume(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if not guild:
            return

        vc = guild.voice_client

        if not isinstance(vc, wavelink.Player):
            await interaction.response.send_message(
                "No music player found.",
                ephemeral=True
            )
            return

        if vc.paused:
            await vc.pause(False)

            button.label = "Pause"

            await interaction.response.edit_message(
                view=self
            )

        else:
            await vc.pause(True)

            button.label = "Resume"

            await interaction.response.edit_message(
                view=self
            )

    # =====================================================
    # SKIP
    # =====================================================

    @discord.ui.button(
        label="Skip",
        style=discord.ButtonStyle.secondary
    )
    async def skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if not guild:
            return

        vc = guild.voice_client

        if isinstance(vc, wavelink.Player):
            await vc.skip(force=True)

        await interaction.response.send_message(
            "⏭ Skipped",
            ephemeral=True
        )

    # =====================================================
    # SHUFFLE
    # =====================================================

    @discord.ui.button(
        label="Shuffle",
        style=discord.ButtonStyle.secondary
    )
    async def shuffle(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        player = self.cog.manager.get_player(
            self.guild_id
        )

        import random

        queue_items = list(player.queue._queue)
        random.shuffle(queue_items)

        player.queue._queue.clear()

        for item in queue_items:
            player.queue._queue.append(item)

        await interaction.response.send_message(
            "🔀 Queue shuffled",
            ephemeral=True
        )