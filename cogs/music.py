import discord
from discord import app_commands
from discord.ext import commands

from core.cog_base import BaseCog

from services.music.manager import music_manager
from services.music.resolver import music_resolver

from services.music.runtime import music_runtime
from services.music.lavalink.bridge import voice_bridge

from ui.music_player import MusicPlayerView


class MusicCog(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)
        self.manager = music_manager

    # =====================================================
    # /PLAY
    # =====================================================

    @app_commands.command(
        name="play",
        description="Play a song or add it to the queue"
    )
    async def play(self, interaction: discord.Interaction, query: str):
        await self.ensure_guild(interaction.guild_id)

        player = self.manager.get_player(interaction.guild_id)

        # -------------------------
        # VOICE CHECK + AUTO JOIN
        # -------------------------
        voice_state = interaction.user.voice

        if not voice_state or not voice_state.channel:
            await self.send_error(interaction, "Join a voice channel first.")
            return

        await voice_bridge.connect(
            interaction.guild,
            voice_state.channel
        )

        # -------------------------
        # START RUNTIME LOOP
        # -------------------------
        await music_runtime.start_guild(interaction.guild_id)

        # -------------------------
        # RESOLVE TRACKS
        # -------------------------
        tracks = await music_resolver.resolve(
            query=query,
            requester_id=interaction.user.id
        )

        if not tracks:
            await self.send_error(interaction, "No results found.")
            return

        for track in tracks:
            player.queue.add(track)

        # auto-start playback state if idle
        if not player.is_playing:
            await player.start()

        # -------------------------
        # UI RESPONSE
        # -------------------------
        embed = discord.Embed(
            title="🎵 Added to Queue",
            description=tracks[0].title,
            color=discord.Color.blurple()
        )

        view = MusicPlayerView(self, interaction.guild_id)

        await interaction.response.send_message(
            embed=embed,
            view=view
        )

    # =====================================================
    # /SKIP
    # =====================================================

    @app_commands.command(
        name="skip",
        description="Skip current track"
    )
    async def skip(self, interaction: discord.Interaction):
        player = self.manager.get_player(interaction.guild_id)

        await player.skip()

        await self.send_success(interaction, "Skipped track")

    # =====================================================
    # /QUEUE
    # =====================================================

    @app_commands.command(
        name="queue",
        description="Show current queue"
    )
    async def queue(self, interaction: discord.Interaction):
        player = self.manager.get_player(interaction.guild_id)

        tracks = player.queue.all()

        if not tracks:
            await self.send_error(interaction, "Queue is empty.")
            return

        desc = "\n".join(
            f"{i+1}. {t.title}" for i, t in enumerate(tracks[:10])
        )

        embed = discord.Embed(
            title="🎶 Queue",
            description=desc,
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    # =====================================================
    # /NOW PLAYING
    # =====================================================

    @app_commands.command(
        name="nowplaying",
        description="Show current track"
    )
    async def nowplaying(self, interaction: discord.Interaction):
        player = self.manager.get_player(interaction.guild_id)

        if not player.current:
            await self.send_error(interaction, "Nothing is playing.")
            return

        embed = discord.Embed(
            title="🎧 Now Playing",
            description=player.current.title,
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    # =====================================================
    # /PAUSE
    # =====================================================

    @app_commands.command(
        name="pause",
        description="Pause playback"
    )
    async def pause(self, interaction: discord.Interaction):
        player = self.manager.get_player(interaction.guild_id)

        player.is_playing = False

        await self.send_success(interaction, "Paused")

    # =====================================================
    # /RESUME
    # =====================================================

    @app_commands.command(
        name="resume",
        description="Resume playback"
    )
    async def resume(self, interaction: discord.Interaction):
        player = self.manager.get_player(interaction.guild_id)

        player.is_playing = True

        await self.send_success(interaction, "Resumed")

    # =====================================================
    # OPTIONAL: FORCE START LOOP (DEBUG / ADMIN)
    # =====================================================

    @app_commands.command(
        name="music_start",
        description="Force start music runtime loop"
    )
    async def music_start(self, interaction: discord.Interaction):
        await music_runtime.start_guild(interaction.guild_id)
        await self.send_success(interaction, "Music loop started")

    # =====================================================
    # OPTIONAL: STOP LOOP
    # =====================================================

    @app_commands.command(
        name="music_stop",
        description="Stop music runtime loop"
    )
    async def music_stop(self, interaction: discord.Interaction):
        music_runtime.stop_guild(interaction.guild_id)
        await self.send_success(interaction, "Music loop stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))