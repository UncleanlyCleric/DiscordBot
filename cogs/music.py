import discord
from discord.ext import commands
import wavelink
from collections import deque


# =====================================================
# 🎼 GUILD PLAYER STATE
# =====================================================
class GuildPlayer:
    def __init__(self):
        self.queue = deque()
        self.history = deque(maxlen=50)
        self.current: wavelink.Playable | None = None
        self.loop_mode = "off"  # off | track | queue


players = {}


def get_player(guild_id: int) -> GuildPlayer:
    if guild_id not in players:
        players[guild_id] = GuildPlayer()
    return players[guild_id]


# =====================================================
# 🎛 UI CONTROLS
# =====================================================
class MusicControls(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(label="⏸", style=discord.ButtonStyle.gray)
    async def pause(self, interaction, button):
        vc = self.ctx.voice_client
        if vc:
            await vc.pause()
        await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
    async def resume(self, interaction, button):
        vc = self.ctx.voice_client
        if vc:
            await vc.resume()
        await interaction.response.defer()

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction, button):
        vc = self.ctx.voice_client
        if vc:
            await vc.stop()
        await interaction.response.defer()

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.red)
    async def stop(self, interaction, button):
        vc = self.ctx.voice_client
        player = get_player(self.ctx.guild.id)

        player.queue.clear()
        player.current = None

        if vc:
            await vc.disconnect()

        await interaction.response.defer()


# =====================================================
# 🎧 MUSIC COG
# =====================================================
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # LAVALINK CONNECT
    # -------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        if not wavelink.Pool.nodes:
            await wavelink.Pool.connect(
                client=self.bot,
                nodes=[
                    wavelink.Node(
                        uri="http://localhost:2333",
                        password="youshallnotpass"
                    )
                ]
            )

    # -------------------------
    # TRACK END HANDLER
    # -------------------------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        vc = payload.player
        if vc:
            await self.play_next(vc, vc.guild.id)

    # -------------------------
    # CORE PLAYER ENGINE
    # -------------------------
    async def play_next(self, vc: wavelink.Player, guild_id: int):
        player = get_player(guild_id)

        # loop current track
        if player.loop_mode == "track" and player.current:
            await vc.play(player.current)
            return

        # queue loop
        if player.loop_mode == "queue" and player.current:
            player.queue.append(player.current)

        if not player.queue:
            player.current = None
            return

        next_track = player.queue.popleft()
        player.current = next_track
        player.history.append(next_track)

        await vc.play(next_track)

    # =====================================================
    # 🎵 PLAY
    # =====================================================
    @commands.hybrid_command(
        name="play",
        description="Play music or add to queue"
    )
    async def play(self, ctx: commands.Context, *, query: str):

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        vc: wavelink.Player = ctx.voice_client

        if not vc:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        player = get_player(ctx.guild.id)

        results = await wavelink.Playable.search(query)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        player.queue.append(track)

        if not vc.playing:
            await self.play_next(vc, ctx.guild.id)

        embed = discord.Embed(
            title="🎶 Added to Queue",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=MusicControls(ctx))

    # =====================================================
    # ⏭ SKIP
    # =====================================================
    @commands.hybrid_command(
        name="skip",
        description="Skip current track"
    )
    async def skip(self, ctx: commands.Context):
        vc = ctx.voice_client
        if vc:
            await vc.stop()
        await ctx.send("⏭ Skipped")

    # =====================================================
    # ⏸ PAUSE
    # =====================================================
    @commands.hybrid_command(
        name="pause",
        description="Pause playback"
    )
    async def pause(self, ctx: commands.Context):
        vc = ctx.voice_client
        if vc:
            await vc.pause()
        await ctx.send("⏸ Paused")

    # =====================================================
    # ▶ RESUME
    # =====================================================
    @commands.hybrid_command(
        name="resume",
        description="Resume playback"
    )
    async def resume(self, ctx: commands.Context):
        vc = ctx.voice_client
        if vc:
            await vc.resume()
        await ctx.send("▶️ Resumed")

    # =====================================================
    # ⏹ STOP
    # =====================================================
    @commands.hybrid_command(
        name="stop",
        description="Stop music and clear queue"
    )
    async def stop(self, ctx: commands.Context):
        vc = ctx.voice_client
        player = get_player(ctx.guild.id)

        player.queue.clear()
        player.current = None

        if vc:
            await vc.disconnect()

        await ctx.send("⏹ Stopped and cleared queue")

    # =====================================================
    # 🔁 LOOP
    # =====================================================
    @commands.hybrid_command(
        name="loop",
        description="Set loop mode: off, track, queue"
    )
    async def loop(self, ctx: commands.Context, mode: str):

        player = get_player(ctx.guild.id)
        mode = mode.lower()

        if mode not in ("off", "track", "queue"):
            return await ctx.send("Use: off, track, queue")

        player.loop_mode = mode
        await ctx.send(f"🔁 Loop set to `{mode}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))