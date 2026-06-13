import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class MusicPlayerView(discord.ui.View):

    def __init__(self, guild_id=None):

        super().__init__(timeout=None)

        if guild_id is None:
            return

        state = music_manager.get_player(guild_id)

        for item in self.children:

            if item.custom_id == "music_loop_track":
                item.style = (
                    discord.ButtonStyle.success
                    if state.loop_track
                    else discord.ButtonStyle.secondary
                )

            elif item.custom_id == "music_loop_queue":
                item.style = (
                    discord.ButtonStyle.success
                    if state.loop_queue
                    else discord.ButtonStyle.secondary
                )

            elif item.custom_id == "music_autoplay":
                item.style = (
                    discord.ButtonStyle.success
                    if getattr(state, "autoplay", False)
                    else discord.ButtonStyle.secondary
                )

            elif item.custom_id == "music_dj_mode":
                item.style = (
                    discord.ButtonStyle.success
                    if getattr(state, "dj_mode", False)
                    else discord.ButtonStyle.secondary
                )

    # =====================================================
    # HELPERS
    # =====================================================

    def _state(self, guild_id: int):
        return music_manager.get_player(guild_id)

    def _refresh_embed(self, guild_id: int):
        state = self._state(guild_id)
        return build_now_playing_embed(state)

    def _is_dj(self, interaction):

        state = self._state(
            interaction.guild.id
        )

        if not getattr(state, "dj_mode", False):
            return True

        if interaction.user.guild_permissions.manage_guild:
            return True

        return False

    async def _deny_dj(self, interaction):

        await interaction.response.send_message(
            "🎧 DJ Mode is enabled.",
            ephemeral=True
        )

    # =====================================================
    # PREVIOUS
    # =====================================================

    @discord.ui.button(
        emoji="⏮",
        style=discord.ButtonStyle.primary,
        custom_id="music_previous",
        row=0
    )
    async def previous(self, interaction, button):

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.previous(player)

        try:
            await interaction.response.defer()
        except Exception:
            pass

    # =====================================================
    # PAUSE / RESUME
    # =====================================================

    @discord.ui.button(
        emoji="⏯",
        style=discord.ButtonStyle.primary,
        custom_id="music_pause_resume",
        row=0
    )
    async def pause_resume(self, interaction, button):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(
                    not player.paused
                )
            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
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

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.skip(player)

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
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

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        player = interaction.guild.voice_client

        if player:
            from services.music.player_engine import engine
            await engine.stop(player)

        try:
            await interaction.response.defer()
        except Exception:
            pass

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

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        state = self._state(
            interaction.guild.id
        )

        state.queue.shuffle()

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # HISTORY
    # =====================================================

    @discord.ui.button(
        emoji="🕘",
        style=discord.ButtonStyle.secondary,
        custom_id="music_history",
        row=1
    )
    async def history(self, interaction, button):

        state = self._state(
            interaction.guild.id
        )

        history = getattr(
            state,
            "history",
            []
        )

        if not history:

            await interaction.response.send_message(
                "No playback history.",
                ephemeral=True
            )
            return

        current = state.current

        lines = []

        if current:

            lines.append(
                f"▶ Current:\n{current.title}\n"
            )

        lines.append(
            "Recently Played:"
        )

        recent = list(
            reversed(history[:-1])
        )[:15]

        for i, track in enumerate(recent):

            lines.append(
                f"{i + 1}. {track.title}"
            )

        await interaction.response.send_message(
            "\n".join(lines),
            ephemeral=True
        )

    # =====================================================
    # TRACK LOOP
    # =====================================================

    @discord.ui.button(
        emoji="🔂",
        style=discord.ButtonStyle.secondary,
        custom_id="music_loop_track",
        row=1
    )
    async def loop_track(self, interaction, button):

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        state = self._state(
            interaction.guild.id
        )

        state.loop_track = not state.loop_track

        if state.loop_track:
            state.loop_queue = False

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # QUEUE LOOP
    # =====================================================

    @discord.ui.button(
        emoji="🔁",
        style=discord.ButtonStyle.secondary,
        custom_id="music_loop_queue",
        row=1
    )
    async def loop_queue(self, interaction, button):

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        state = self._state(
            interaction.guild.id
        )

        state.loop_queue = not state.loop_queue

        if state.loop_queue:
            state.loop_track = False

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # AUTOPLAY
    # =====================================================

    @discord.ui.button(
        emoji="♾️",
        style=discord.ButtonStyle.secondary,
        custom_id="music_autoplay",
        row=1
    )
    async def autoplay(self, interaction, button):

        state = self._state(
            interaction.guild.id
        )

        state.autoplay = not getattr(
            state,
            "autoplay",
            False
        )

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # DJ MODE
    # =====================================================

    @discord.ui.button(
        emoji="🎧",
        style=discord.ButtonStyle.secondary,
        custom_id="music_dj_mode",
        row=1
    )
    async def dj_mode(self, interaction, button):

        state = self._state(
            interaction.guild.id
        )

        state.dj_mode = not getattr(
            state,
            "dj_mode",
            False
        )

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # VOLUME DOWN
    # =====================================================

    @discord.ui.button(
        emoji="🔉",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_down",
        row=0
    )
    async def volume_down(self, interaction, button):

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        player = interaction.guild.voice_client

        state = self._state(
            interaction.guild.id
        )

        if player:

            try:

                state.volume = max(
                    0,
                    state.volume - 10
                )

                await player.set_volume(
                    state.volume
                )

            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

    # =====================================================
    # VOLUME UP
    # =====================================================

    @discord.ui.button(
        emoji="🔊",
        style=discord.ButtonStyle.secondary,
        custom_id="music_volume_up",
        row=0
    )
    async def volume_up(self, interaction, button):

        if not self._is_dj(interaction):
            await self._deny_dj(interaction)
            return

        player = interaction.guild.voice_client

        state = self._state(
            interaction.guild.id
        )

        if player:

            try:

                state.volume = min(
                    200,
                    state.volume + 10
                )

                await player.set_volume(
                    state.volume
                )

            except Exception:
                pass

        await interaction.response.edit_message(
            embed=self._refresh_embed(
                interaction.guild.id
            ),
            view=MusicPlayerView(
                interaction.guild.id
            )
        )

