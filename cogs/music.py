import discord
from discord.ext import commands
import wavelink
import os
import random
from collections import deque

from utils.resolver import resolve_music


# =====================================================
# 🎼 GUILD PLAYER STATE
# =====================================================
class GuildPlayer:
    def __init__(self):
        self.queue = deque()
        self.history = deque(maxlen=50)
        self.current: wavelink.Playable | None = None
        self.loop_mode = "off"

        # 📻 RADIO MODE
        self.radio_enabled = False
        self.radio_seed = None


players = {}


def get_player(guild_id: int) -> GuildPlayer:
    if guild_id not in players:
        players[guild_id] = GuildPlayer()
    return players[guild_id]


# =====================================================
# 🎧 MUSIC COG (SPOTIFY REMOVED)
# =====================================================
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._lavalink_connected = False

    # =====================================================
    # LAVALINK CONNECT (SAFE, ONCE ONLY)
    # =====================================================
    @commands.Cog.listener()
    async def on_ready(self):
        if self._lavalink_connected:
            return

        self._lavalink_connected = True

        uri = os.getenv("LAVALINK_URI")
        password = os.getenv("LAVALINK_PASSWORD")

        if not uri or not password:
            print("[LAVALINK] Missing config - music disabled")
            return

        try:
            await wavelink.Pool.connect(
                client=self.bot,
                nodes=[
                    wavelink.Node(
                        uri=uri,
                        password=password
                    )
                ]
            )
            print("[LAVALINK] Connected successfully")

        except Exception as e:
            print("[LAVALINK] Connection failed:", e)

    # =====================================================
    # TRACK END HANDLER
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        vc = payload.player
        if vc:
            await self.play_next(vc, vc.guild.id)

    # =====================================================
    # CORE ENGINE
    # =====================================================
    async def play_next(self, vc: wavelink.Player, guild_id: int):
        player = get_player(guild_id)

        # loop track
        if player.loop_mode == "track" and player.current:
            await vc.play(player.current)
            return

        # queue loop
        if player.loop_mode == "queue" and player.current:
            player.queue.append(player.current)

        # normal queue
        if player.queue:
            next_track = player.queue.popleft()

        # 📻 RADIO MODE
        elif player.radio_enabled and player.radio_seed:
            results = await wavelink.Playable.search(player.radio_seed)
            if results:
                next_track = random.choice(results[:5])
            else:
                return
        else:
            player.current = None
            return

        player.current = next_track
        player.history.append(next_track)

        await vc.play(next_track)

    # =====================================================
    # 🎵 PLAY
    # =====================================================
    @commands.hybrid_command(name="play", description="Play music or add to queue")
    async def play(self, ctx: commands.Context, *, query: str):

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        vc: wavelink.Player = ctx.voice_client

        if not vc:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        player = get_player(ctx.guild.id)

        query = await resolve_music(query)

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

        await ctx.send(embed=embed)

    # =====================================================
    # 📻 RADIO
    # =====================================================
    @commands.hybrid_command(name="radio")
    async def radio(self, ctx: commands.Context, *, query: str = None):

        player = get_player(ctx.guild.id)

        if query:
            player.radio_seed = await resolve_music(query)
            player.radio_enabled = True
            await ctx.send(f"📻 Radio started from: `{query}`")
        else:
            player.radio_enabled = not player.radio_enabled
            await ctx.send(f"📻 Radio: `{player.radio_enabled}`")

    # =====================================================
    # CONTROLS
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.stop()
        await ctx.send("⏭ Skipped")

    @commands.hybrid_command(name="pause")
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.pause()
        await ctx.send("⏸ Paused")

    @commands.hybrid_command(name="resume")
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.resume()
        await ctx.send("▶️ Resumed")

    @commands.hybrid_command(name="stop")
    async def stop(self, ctx):
        vc = ctx.voice_client
        player = get_player(ctx.guild.id)

        player.queue.clear()
        player.current = None

        if vc:
            await vc.disconnect()

        await ctx.send("⏹ Stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))