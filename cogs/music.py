import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from core.cog_base import BaseCog

from services.music.manager import music_manager
from services.music.resolver import music_resolver
from services.music.controller import music_controller
from services.music.lavalink.bridge import voice_bridge
from ui.music_player import MusicPlayerView


class MusicCog(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)
        self.manager = music_manager

    # =====================================================
    # SAFE LAVALINK CHECK
    # =====================================================
    def lavalink_ready(self) -> bool:
        return bool(wavelink.Pool.nodes)

    # =====================================================
    # /PLAY
    # =====================================================
    @app_commands.command(name="play", description="Play a song or add to queue")
    async def play(self, interaction: discord.Interaction, query: str):

        await self.ensure_guild(interaction.guild_id)

        player = self.manager.get_player(interaction.guild_id)

        if not self.lavalink_ready():
            await self.send_error(interaction, "🎵 Music system is still starting.")
            return

        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            await self.send_error(interaction, "Join a voice channel first.")
            return

        try:
            await voice_bridge.connect(interaction.guild, voice_state.channel)
        except Exception as e:
            await self.send_error(interaction, f"Failed to connect: {e}")
            return

        try:
            tracks = await music_resolver.resolve(
                query=query,
                requester_id=interaction.user.id
            )
        except Exception as e:
            await self.send_error(interaction, f"Search failed: {e}")
            return

        if not tracks:
            await self.send_error(interaction, "No results found.")
            return

        # =====================================================
        # QUEUE ONLY (controller handles playback)
        # =====================================================
        player.queue.add_many(tracks)

        # start single playback engine
        await music_controller.start_loop(interaction.guild_id)

        embed = discord.Embed(
            title="🎵 Added to Queue",
            description=tracks[0].title,
            color=discord.Color.blurple()
        )

        view = MusicPlayerView(self, interaction.guild_id)

        await interaction.response.send_message(embed=embed, view=view)

    # =====================================================
    # /SKIP (FIXED - controller owns playback)
    # =====================================================
    @app_commands.command(name="skip", description="Skip current track")
    async def skip(self, interaction: discord.Interaction):

        vc = interaction.guild.voice_client

        try:
            if vc:
                await vc.stop()
        except Exception:
            pass

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # =====================================================
    # /QUEUE
    # =====================================================
    @app_commands.command(name="queue", description="Show queue")
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
    @app_commands.command(name="nowplaying", description="Current track")
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
    # /PAUSE (REAL LAVALINK CONTROL)
    # =====================================================
    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):

        vc = interaction.guild.voice_client

        if not vc:
            await self.send_error(interaction, "Nothing is playing.")
            return

        try:
            await vc.pause(True)
        except Exception as e:
            await self.send_error(interaction, f"Pause failed: {e}")
            return

        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    # =====================================================
    # /RESUME (REAL LAVALINK CONTROL)
    # =====================================================
    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):

        vc = interaction.guild.voice_client

        if not vc:
            await self.send_error(interaction, "Nothing is playing.")
            return

        try:
            await vc.pause(False)
        except Exception as e:
            await self.send_error(interaction, f"Resume failed: {e}")
            return

        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    # =====================================================
    # /MUSIC_START
    # =====================================================
    @app_commands.command(name="music_start", description="Force start runtime")
    async def music_start(self, interaction: discord.Interaction):
        await music_controller.start_loop(interaction.guild_id)
        await self.send_success(interaction, "Music loop started")

    # =====================================================
    # /MUSIC_STOP
    # =====================================================
    @app_commands.command(name="music_stop", description="Stop music and disconnect")
    async def music_stop(self, interaction: discord.Interaction):

        music_controller.stop_loop(interaction.guild_id)

        player = self.manager.get_player(interaction.guild_id)
        player.current = None
        player.queue.clear()

        vc = interaction.guild.voice_client
        if vc:
            try:
                await vc.stop()
                await vc.disconnect()
            except Exception:
                pass

        await self.send_success(interaction, "🛑 Stopped music and disconnected")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))