import discord
from discord import app_commands
from discord.ext import commands

import wavelink

from services.music.resolver import music_resolver
from services.music.manager import music_manager
from services.music.player_engine import engine

# OPTIONAL UI (safe import)
try:
    from ui.music_player_view import MusicPlayerView
    from ui.music_player_view import progress_bar
except Exception:
    MusicPlayerView = None


def build_now_playing(track, requester_id: int):
    embed = discord.Embed(
        title="🎧 Now Playing",
        description=f"**{track.title}**",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Author",
        value=getattr(track, "author", "Unknown"),
        inline=True
    )

    embed.add_field(
        name="Requested by",
        value=f"<@{requester_id}>",
        inline=True
    )

    embed.add_field(
        name="Source",
        value=track.uri or "Unknown",
        inline=False
    )

    return embed


class MusicCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.now_playing_message = {}  # guild_id -> message

    # =====================================================
    # INTERNAL: SAFE PLAYER GET
    # =====================================================
    async def _get_player(self, interaction: discord.Interaction):
        if not interaction.guild:
            raise RuntimeError("Guild only command")

        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            return None

        channel = voice_state.channel

        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            player = await channel.connect(cls=wavelink.Player)

        return player

    # =====================================================
    # PLAY
    # =====================================================
    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        player = await self._get_player(interaction)

        if not player:
            return await interaction.followup.send("Join a voice channel first.")

        tracks = await music_resolver.resolve(query, interaction.user.id)

        if not tracks:
            return await interaction.followup.send("No results.")

        primary = tracks[0]

        await engine.enqueue(player, primary)

        # prefetch
        for t in tracks[1:3]:
            await engine.enqueue(player, t)

        # =====================================================
        # UI: NOW PLAYING
        # =====================================================
        embed = build_now_playing(primary, interaction.user.id)

        view = None
        if MusicPlayerView:
            view = MusicPlayerView(self.bot, interaction.guild.id)

        msg = await interaction.followup.send(
            embed=embed,
            view=view
        )

        self.now_playing_message[interaction.guild.id] = msg

    # =====================================================
    # STOP
    # =====================================================
    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            await engine.stop(player)

            try:
                await player.disconnect()
            except Exception:
                pass

        # clear UI
        self.now_playing_message.pop(interaction.guild_id, None)

        await interaction.response.send_message("🛑 Stopped", ephemeral=True)

    # =====================================================
    # SKIP
    # =====================================================
    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            await engine.skip(player)

        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    # =====================================================
    # PAUSE
    # =====================================================
    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(True)
            except Exception:
                pass

        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    # =====================================================
    # RESUME
    # =====================================================
    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):

        player = interaction.guild.voice_client

        if player:
            try:
                await player.pause(False)
            except Exception:
                pass

        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    # =====================================================
    # QUEUE
    # =====================================================
    @app_commands.command(name="queue")
    async def queue(self, interaction: discord.Interaction):

        state = music_manager.get_player(interaction.guild_id)

        tracks = state.queue.all()

        if not tracks:
            return await interaction.response.send_message("Queue empty.")

        msg = "\n".join(
            f"{i+1}. {t.title}"
            for i, t in enumerate(tracks[:10])
        )

        await interaction.response.send_message(msg)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))