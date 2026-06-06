import discord


class PlayerView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    def gm(self):
        cog = self.bot.get_cog("Music")
        return cog.get_player(self.guild_id)

    # =====================================================
    # ⏮ RESTART TRACK
    # =====================================================
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def restart(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        if gm.player and gm.now_playing:
            try:
                await gm.player.seek(0)
            except Exception:
                pass

        await interaction.response.defer()

    # =====================================================
    # ⏯ PLAY / PAUSE
    # =====================================================
    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        if not gm.player:
            return await interaction.response.defer()

        try:
            if gm.player.paused:
                await gm.player.pause(False)
            else:
                await gm.player.pause(True)
        except Exception:
            pass

        await interaction.response.defer()

    # =====================================================
    # ⏭ SKIP
    # =====================================================
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        if gm.player:
            await gm.player.stop()

        await interaction.response.defer()

    # =====================================================
    # 🔀 SHUFFLE
    # =====================================================
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        count = await gm.shuffle()

        await interaction.response.send_message(
            f"🔀 Shuffled {count} tracks.",
            ephemeral=True
        )

    # =====================================================
    # 📜 QUEUE
    # =====================================================
    @discord.ui.button(emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def queue(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        items = list(gm.queue._queue)[:10]

        if not items:
            return await interaction.response.send_message(
                "Queue is empty.",
                ephemeral=True
            )

        msg = "\n".join(
            f"• {getattr(t, 'title', 'Unknown')}"
            for t in items
        )

        await interaction.response.send_message(
            f"📜 **Next Up:**\n{msg}",
            ephemeral=True
        )

    # =====================================================
    # 🔉 VOLUME DOWN
    # =====================================================
    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        if gm.player:
            try:
                gm.player.volume = max(0, gm.player.volume - 10)
            except Exception:
                pass

        await interaction.response.defer()

    # =====================================================
    # 🔊 VOLUME UP
    # =====================================================
    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        if gm.player:
            try:
                gm.player.volume = min(100, gm.player.volume + 10)
            except Exception:
                pass

        await interaction.response.defer()

    # =====================================================
    # ⏹ STOP
    # =====================================================
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def stop(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        gm = self.gm()

        await gm.stop()

        await interaction.response.defer()