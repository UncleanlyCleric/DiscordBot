import discord
from discord.ext import commands
import wavelink
import asyncio

from music.guild_music import GuildMusic
from utils.resolver import resolve_music


players: dict[int, GuildMusic] = {}


def get_player(guild_id: int) -> GuildMusic:
    if guild_id not in players:
        players[guild_id] = GuildMusic(guild_id)
    return players[guild_id]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # DEBUG TRACK END (FIXED)
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        print("[DEBUG] Track ended event fired")

        try:
            guild = payload.player.guild
            gm = get_player(guild.id)

            print("[DEBUG] Calling play_next()")
            await gm.play_next()

        except Exception as e:
            print("[ERROR] track_end handler failed:", e)

        asyncio.create_task(self.auto_disconnect(payload.player.guild.id))

    # =====================================================
    # AUTO DISCONNECT (FIXED SAFE VERSION)
    # =====================================================
    async def auto_disconnect(self, guild_id: int):
        await asyncio.sleep(60)

        gm = get_player(guild_id)

        if gm.is_idle() and gm.player:
            print("[DEBUG] Auto disconnect triggered")

            try:
                await gm.player.disconnect()
            except Exception as e:
                print("[ERROR] disconnect failed:", e)

            gm.player = None

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
    # PLAY COMMAND (FIXED + DEBUGGED)
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        print(f"[DEBUG] play command received: {query}")

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # connect if needed
        if not gm.player:
            print("[DEBUG] Connecting to voice...")
            gm.player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        query = await resolve_music(query)
        print(f"[DEBUG] Resolved query: {query}")

        results = await wavelink.Playable.search(query)

        if not results:
            print("[DEBUG] No results found")
            return await ctx.send("No results found.")

        track = results[0]

        print(f"[DEBUG] Adding track: {track.title}")
        await gm.add(track)

        print("[DEBUG] Queue state:", gm.queue)

        # IMPORTANT FIX: force play if nothing is playing
        if not gm.current:
            print("[DEBUG] Nothing currently playing → calling play_next()")
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

    # =====================================================
    # SKIP (SAFE)
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):
        gm = get_player(ctx.guild.id)

        print("[DEBUG] skip command")

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # =====================================================
    # STOP (SAFE)
    # =====================================================
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):
        gm = get_player(ctx.guild.id)

        print("[DEBUG] stop command")

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

        print(f"[DEBUG] radio set: {query}")

        await ctx.send(f"📻 Radio started: `{query}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))