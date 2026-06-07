import discord
from discord.ext import commands
import wavelink
import tempfile

from music.manager import MusicManager


# =====================================================
# GLOBAL MANAGER REGISTRY
# =====================================================
MANAGERS: dict[int, MusicManager] = {}


def get_manager(guild_id: int) -> MusicManager:
    if guild_id not in MANAGERS:
        MANAGERS[guild_id] = MusicManager(guild_id)
    return MANAGERS[guild_id]


# =====================================================
# MUSIC COG
# =====================================================
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =================================================
    # VOICE HELPERS
    # =================================================
    async def get_player(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("❌ Join a voice channel first.")
            return None

        player: wavelink.Player = ctx.voice_client

        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        return player

    # =================================================
    # PLAY (QUEUE SYSTEM)
    # =================================================
    @commands.hybrid_command(name="play", description="Play music from search or URL")
    async def play(self, ctx: commands.Context, *, query: str):

        player = await self.get_player(ctx)
        if not player:
            return

        manager = get_manager(ctx.guild.id)
        manager.bind_player(player)

        tracks = await wavelink.Playable.search(query)

        if not tracks:
            await ctx.send("❌ No results found.")
            return

        track = tracks[0]

        await manager.add(track)

        await ctx.send(f"🎵 Added to queue: **{track.title}**")

    # =================================================
    # PLAY FILE (LOCAL UPLOAD)
    # =================================================
    @commands.hybrid_command(name="playfile", description="Play uploaded audio file")
    async def playfile(self, ctx: commands.Context):

        if not ctx.message.attachments:
            await ctx.send("📁 Attach an audio file.")
            return

        attachment = ctx.message.attachments[0]

        if not any(attachment.filename.endswith(x) for x in [".mp3", ".wav", ".ogg", ".m4a"]):
            await ctx.send("❌ Unsupported file type.")
            return

        player = await self.get_player(ctx)
        if not player:
            return

        manager = get_manager(ctx.guild.id)
        manager.bind_player(player)

        data = await attachment.read()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=attachment.filename)
        tmp.write(data)
        tmp.close()

        track = wavelink.FFmpegAudio(tmp.name)
        track.title = attachment.filename

        await manager.add(track)

        await ctx.send(f"🎶 Added file to queue: `{attachment.filename}`")

    # =====================================================
    # SKIP
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):

        manager = get_manager(ctx.guild.id)

        await manager.skip()

        await ctx.send("⏭ Skipped.")

    # =====================================================
    # PAUSE / RESUME
    # =====================================================
    @commands.hybrid_command(name="pause")
    async def pause(self, ctx: commands.Context):

        player: wavelink.Player = ctx.voice_client
        if player:
            await player.pause(True)
            await ctx.send("⏸ Paused.")

    @commands.hybrid_command(name="resume")
    async def resume(self, ctx: commands.Context):

        player: wavelink.Player = ctx.voice_client
        if player:
            await player.pause(False)
            await ctx.send("▶️ Resumed.")

    # =====================================================
    # NOW PLAYING
    # =====================================================
    @commands.hybrid_command(name="nowplaying")
    async def nowplaying(self, ctx: commands.Context):

        manager = get_manager(ctx.guild.id)

        if not manager.current:
            await ctx.send("Nothing is playing.")
            return

        track = manager.current

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=track.title,
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed)

    # =====================================================
    # STOP
    # =====================================================
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):

        manager = get_manager(ctx.guild.id)

        await manager.stop()

        await ctx.send("⏹ Stopped and cleared queue.")

    # =====================================================
    # 🔥 FIXED WAVELINK EVENT (NO Pool.event)
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):

        player = payload.player
        if not player:
            return

        manager = MANAGERS.get(player.guild.id)
        if not manager:
            return

        await manager.play_next()


# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))