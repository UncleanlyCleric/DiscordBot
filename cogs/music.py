import discord
from discord.ext import commands
import wavelink
import asyncio

from music.manager import MusicManager


players: dict[int, MusicManager] = {}


def get_player(guild_id: int) -> MusicManager:
    if guild_id not in players:
        players[guild_id] = MusicManager(guild_id)
    return players[guild_id]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # TRACK END (SAFE)
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        try:
            gm = get_player(payload.player.guild.id)
            await gm.play_next()
        except Exception as e:
            print("[ERROR] track_end:", e)

    # =====================================================
    # EMBED
    # =====================================================
    def now_playing(self, track):
        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.blurple()
        )

        if getattr(track, "uri", None):
            embed.add_field(name="Link", value=f"[Open]({track.uri})", inline=False)

        return embed

    # =====================================================
    # PLAY (FULL FIX)
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        # 🔥 FIX: slash timeout prevention
        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # =====================================================
        # SAFE VOICE HANDLING
        # =====================================================
        voice = ctx.voice_client

        if not voice:
            voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        else:
            if voice.channel != ctx.author.voice.channel:
                await voice.move_to(ctx.author.voice.channel)

        gm.player = voice

        # =====================================================
        # RESOLVE QUERY
        # =====================================================
        query = await resolve_music(query)

        try:
            results = await asyncio.wait_for(
                wavelink.Playable.search(query),
                timeout=10
            )
        except asyncio.TimeoutError:
            return await ctx.send("Search timed out.")

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        await gm.add(track)

        if not gm.now_playing:
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

    # =====================================================
    # SKIP
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):

        gm = get_player(ctx.guild.id)

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # =====================================================
    # STOP
    # =====================================================
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):

        gm = get_player(ctx.guild.id)
        await gm.stop()

        await ctx.send("⏹ Stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))