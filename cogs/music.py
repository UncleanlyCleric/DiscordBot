import discord
from discord.ext import commands
import wavelink
import asyncio

from music.manager import MusicManager
from utils.resolver import resolve_music


players: dict[int, MusicManager] = {}


def get_player(guild_id: int) -> MusicManager:
    if guild_id not in players:
        players[guild_id] = MusicManager(guild_id)
    return players[guild_id]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # TRACK END EVENT (SAFE + DEBUG)
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        try:
            print("[DEBUG] Track ended")

            gm = get_player(payload.player.guild.id)
            await gm.play_next()

        except Exception as e:
            print("[ERROR] track_end failed:", e)

    # =====================================================
    # NOW PLAYING EMBED
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
    # PLAY COMMAND (FULL FIX)
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # =====================================================
        # 🔥 FIX: SAFE VOICE HANDLING (NO MORE CRASH)
        # =====================================================
        voice = ctx.voice_client

        if not voice:
            print("[DEBUG] Connecting to voice...")
            voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        else:
            print("[DEBUG] Reusing existing voice client")

            if voice.channel != ctx.author.voice.channel:
                print("[DEBUG] Moving voice channel")
                await voice.move_to(ctx.author.voice.channel)

        gm.player = voice

        # =====================================================
        # RESOLVE QUERY
        # =====================================================
        query = await resolve_music(query)
        print(f"[DEBUG] Resolved query: {query}")

        results = await wavelink.Playable.search(query)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        print(f"[DEBUG] Queuing track: {track.title}")

        await gm.add(track)

        # =====================================================
        # START PLAYBACK IF NOTHING IS PLAYING
        # =====================================================
        if not gm.now_playing:
            print("[DEBUG] Starting playback...")
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

    # =====================================================
    # SKIP
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):

        gm = get_player(ctx.guild.id)

        print("[DEBUG] Skip command")

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # =====================================================
    # STOP
    # =====================================================
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):

        gm = get_player(ctx.guild.id)

        print("[DEBUG] Stop command")

        await gm.stop()

        await ctx.send("⏹ Stopped")

    # =====================================================
    # RADIO
    # =====================================================
    @commands.hybrid_command(name="radio")
    async def radio(self, ctx: commands.Context, *, query: str = None):

        gm = get_player(ctx.guild.id)

        if not query:
            gm.radio_enabled = not gm.radio_enabled
            return await ctx.send(f"📻 Radio: `{gm.radio_enabled}`")

        gm.radio_enabled = True
        gm.radio_seed = query

        print(f"[DEBUG] Radio set: {query}")

        await ctx.send(f"📻 Radio started: `{query}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))