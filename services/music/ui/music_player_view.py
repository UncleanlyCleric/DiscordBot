import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # HELPERS
    # =====================================================

    def _state(self, guild_id: int):
        return music_manager.get_player(guild_id)

    def _refresh_embed(self, guild_id: int):
        state = self._state(guild_id)
        return build_now_playing_embed(state)

    # =====================================================
    # PAUSE / RESUME
    # =====================================================

    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.secondary,
        custom_id="music_pause_resume",
        row=0
    )
    async def pause_resume(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(not player.paused)
            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    # =====================================================
    # SKIP
    # =====================================================

    @discord.ui.button(
        emoji="⏭",
        style=discord.ButtonStyle.primary,
        custom_id="music_skip",
        row=0
    )
    async def skip(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.skip(player)

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    # =====================================================
    # STOP
    # =====================================================

    @discord.ui.button(
        emoji="⏹",
        style=discord.ButtonStyle.danger,
        custom_id="music_stop",
        row=0
    )
    async def stop(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.stop(player)

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    # =====================================================
    # SHUFFLE
    # =====================================================

    @discord.ui.button(
        emoji="🔀",
        style=discord.ButtonStyle.secondary,
        custom_id="music_shuffle",
        row=1
    )
    async def shuffle(self, interaction, button):

        state = self._state(interaction.guild.id)

        state.queue.shuffle()

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    # =====================================================
    # QUEUE
    # =====================================================

    @discord.ui.button(
        emoji="📜",
        style=discord.ButtonStyle.primary,
        custom_id="music_queue",
        row=1
    )
    async def queue(self, interaction, button):

        state = self._state(interaction.guild.id)

        tracks = state.queue.first(15)

        if not tracks:

            text = "Queue empty."

        else:

            text = "\n".join(
                f"{i + 1}. {track.title}"
                for i, track in enumerate(tracks)
            )

        await interaction.response.send_message(
            text,
            ephemeral=True
        )

    # =====================================================
    # VOLUME DOWN
    # =====================================================

    @discord.ui.button(
        emoji="🔉",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_down",
        row=2
    )
    async def volume_down(self, interaction, button):

        player = interaction.guild.voice_client

        if player:

            try:

                current = getattr(player, "volume", 100)

                new_volume = max(0, current - 10)

                await player.set_volume(new_volume)

            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )

    # =====================================================
    # VOLUME UP
    # =====================================================

    @discord.ui.button(
        emoji="🔊",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_up",
        row=2
    )
    async def volume_up(self, interaction, button):

        player = interaction.guild.voice_client

        if player:

            try:

                current = getattr(player, "volume", 100)

                new_volume = min(200, current + 10)

                await player.set_volume(new_volume)

            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(interaction.guild.id),
            view=self
        )