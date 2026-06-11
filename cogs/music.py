import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    async def _get_player(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.guild:
            return None

        voice = interaction.user.voice

        if not voice or not voice.channel:
            return None

        player = interaction.guild.voice_client

        if not player:

            player = await voice.channel.connect(
                cls=wavelink.Player
            )

        return player

    # =====================================================
    @app_commands.command(name="play")
    async def play(
        self,
        interaction: discord.Interaction,
        query: str
    ):

        await interaction.response.defer()

        player = await self._get_player(
            interaction
        )

        if not player:
            return await interaction.followup.send(
                "Join a voice channel first."
            )

        state = music_manager.get_player(
            interaction.guild_id
        )

        state.player_channel_id = (
            interaction.channel.id
        )

        tracks = await music_resolver.resolve(
            query,
            interaction.user.id
        )

        if not tracks:
            return await interaction.followup.send(
                "No results."
            )

        for track in tracks:
            await engine.enqueue(
                player,
                track
            )

        await engine.start(player)

        await interaction.followup.send(
            f"🎵 Queued: **{tracks[0].title}**"
            + (
                f" (+{len(tracks)-1})"
                if len(tracks) > 1
                else ""
            ),
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="stop")
    async def stop(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            await engine.stop(player)

        await interaction.followup.send(
            "🛑 Stopped",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="skip")
    async def skip(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:
            await engine.skip(player)

        await interaction.followup.send(
            "⏭ Skipped",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="pause")
    async def pause(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:

            try:
                await player.pause(True)
            except Exception:
                pass

        await interaction.followup.send(
            "⏸ Paused",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="resume")
    async def resume(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        player = interaction.guild.voice_client

        if player:

            try:
                await player.pause(False)
            except Exception:
                pass

        await interaction.followup.send(
            "▶ Resumed",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="shuffle")
    async def shuffle(
        self,
        interaction: discord.Interaction
    ):

        state = music_manager.get_player(
            interaction.guild_id
        )

        if len(state.queue) < 2:
            return await interaction.response.send_message(
                "Need at least 2 queued tracks.",
                ephemeral=True
            )

        state.queue.shuffle()

        await interaction.response.send_message(
            "🔀 Queue shuffled.",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="volume")
    async def volume(
        self,
        interaction: discord.Interaction,
        percent: app_commands.Range[int, 1, 200]
    ):

        player = interaction.guild.voice_client

        if not player:
            return await interaction.response.send_message(
                "Nothing is playing.",
                ephemeral=True
            )

        await player.set_volume(percent)

        await interaction.response.send_message(
            f"🔊 Volume set to {percent}%",
            ephemeral=True
        )

    # =====================================================
    @app_commands.command(name="queue")
    async def queue(
        self,
        interaction: discord.Interaction
    ):

        state = music_manager.get_player(
            interaction.guild_id
        )

        tracks = state.queue.first(15)

        if not tracks:

            current = getattr(
                state,
                "current",
                None
            )

            if current:
                return await interaction.response.send_message(
                    f"▶ Now Playing\n\n{current.title}"
                )

            return await interaction.response.send_message(
                "Queue empty."
            )

        lines = []

        current = getattr(
            state,
            "current",
            None
        )

        if current:
            lines.append(
                f"▶ **Now Playing**\n{current.title}\n"
            )

        lines.append(
            "**Up Next**"
        )

        for i, track in enumerate(
            tracks,
            start=1
        ):
            lines.append(
                f"{i}. {track.title}"
            )

        await interaction.response.send_message(
            "\n".join(lines)
        )

    # =====================================================
    # TRACK START
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self,
        payload
    ):
        pass

    # =====================================================
    # TRACK END
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self,
        payload
    ):

        try:

            await engine.handle_track_end(
                payload.player
            )

        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(
        MusicCog(bot)
    )