import discord


class PlayerPanelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    # =====================================================
    # GET MANAGER
    # =====================================================
    def gm(self):
        cog = self.bot.get_cog("Music")
        return cog.get_player(self.guild_id)

    # =====================================================
    # EMBED BUILDER
    # =====================================================
    def build_embed(self):
        gm = self.gm()

        embed = discord.Embed(
            title="🎧 Music Panel",
            color=discord.Color.blurple()
        )

        # =========================
        # NOW PLAYING
        # =========================
        if gm.current:
            t = gm.current
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{getattr(t, 'title', 'Unknown')}**",
                inline=False
            )
        else:
            embed.add_field(
                name="🎵 Now Playing",
                value="Nothing playing",
                inline=False
            )

        # =========================
        # HISTORY
        # =========================
        if gm.history:
            last = gm.history[-3:]
            history_text = "\n".join(
                f"⏮ {getattr(t, 'title', 'Unknown')}" for t in reversed(last)
            )
        else:
            history_text = "None"

        embed.add_field(
            name="🕘 History",
            value=history_text,
            inline=False
        )

        # =========================
        # QUEUE
        # =========================
        queue_items = gm.get_queue_snapshot(8)

        if queue_items:
            queue_text = "\n".join(
                f"• {getattr(t, 'title', 'Unknown')}"
                for t in queue_items
            )
        else:
            queue_text = "Empty"

        embed.add_field(
            name="📥 Queue",
            value=queue_text,
            inline=False
        )

        return embed

    # =====================================================
    # ⏮ BACK
    # =====================================================
    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        await gm.previous()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # =====================================================
    # ⏯ PLAY/PAUSE
    # =====================================================
    @discord.ui.button(label="⏯", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()

        if gm.player.paused:
            await gm.player.pause(False)
        else:
            await gm.player.pause(True)

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # =====================================================
    # ⏭ SKIP
    # =====================================================
    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        await gm.skip()

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # =====================================================
    # ⏹ STOP
    # =====================================================
    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        await gm.stop()

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Stopped",
                description="Playback ended.",
                color=discord.Color.red()
            ),
            view=None
        )

    # =====================================================
    # 🔀 SHUFFLE
    # =====================================================
    @discord.ui.button(label="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):

        gm = self.gm()
        await gm.shuffle()

        await interaction.response.edit_message(embed=self.build_embed(), view=self)