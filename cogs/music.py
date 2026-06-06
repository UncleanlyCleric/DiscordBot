import discord
from discord.ext import commands
import wavelink
import asyncio
import logging

from music.manager import MusicManager


# =====================================================
# LOGGER
# =====================================================
log = logging.getLogger("music")
log.setLevel(logging.INFO)


players: dict[int, MusicManager] = {}


def get_player(guild_id: int) -> MusicManager:
    if guild_id not in players:
        players[guild_id] = MusicManager(guild_id)
    return players[guild_id]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # TRACK END
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        try:
            log.info("[EVENT] track_end fired")

            gm = get_player(payload.player.guild.id)
            await gm.play_next()

        except Exception as e:
            log.error(f"track_end error: {e}")

    # =====================================================
    # EMBED
    # =====================================================
    def now_playing(self, track):
        return discord.Embed(
            title="🎶 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.blurple()
        )

    # =====================================================
    # PLAY COMMAND (FULL DEBUG VERSION)
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        log.info("========== PLAY COMMAND START ==========")

        # slash safety
        if ctx.interaction:
            log.info("[DEFER] deferring interaction")
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            log.warning("[VOICE] user not in voice")
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # =====================================================
        # VOICE DEBUG SECTION
        # =====================================================
        log.info("[VOICE] checking voice state")

        voice = ctx.voice_client

        try:
            log.info("[VOICE] step A - before connect logic")

            if voice and voice.is_connected():
                log.info("[VOICE] reuse existing voice client")

                if voice.channel != ctx.author.voice.channel:
                    log.info("[VOICE] moving channel")
                    await voice.move_to(ctx.author.voice.channel)

            else:
                log.info("[VOICE] connecting to voice channel")

                voice = await asyncio.wait_for(
                    ctx.author.voice.channel.connect(cls=wavelink.Player),
                    timeout=10
                )

            log.info("[VOICE] connected successfully")

        except asyncio.TimeoutError:
            log.error("[VOICE] TIMEOUT while connecting")
            return await ctx.send("❌ Voice connection timed out.")
        except Exception as e:
            log.error(f"[VOICE] ERROR: {e}")
            return await ctx.send(f"❌ Voice error: {e}")

        gm.player = voice

        # =====================================================
        # RESOLVE QUERY
        # =====================================================
        try:
            log.info(f"[SEARCH] resolving query: {query}")

            query = await resolve_music(query)

            log.info(f"[SEARCH] resolved: {query}")

            results = await asyncio.wait_for(
                wavelink.Playable.search(query),
                timeout=10
            )

            log.info(f"[SEARCH] results found: {len(results)}")

        except asyncio.TimeoutError:
            log.error("[SEARCH] TIMEOUT")
            return await ctx.send("❌ Search timed out.")
        except Exception as e:
            log.error(f"[SEARCH] ERROR: {e}")
            return await ctx.send("❌ Search failed.")

        if not results:
            log.warning("[SEARCH] no results")
            return await ctx.send("No results found.")

        track = results[0]

        log.info(f"[QUEUE] adding track: {track.title}")

        await gm.add(track)

        if not gm.now_playing:
            log.info("[PLAY] starting playback")
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

        log.info("========== PLAY COMMAND END ==========")

    # =====================================================
    # SKIP
    # =====================================================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):

        log.info("[SKIP] command triggered")

        gm = get_player(ctx.guild.id)

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # =====================================================
    # STOP
    # =====================================================
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):

        log.info("[STOP] command triggered")

        gm = get_player(ctx.guild.id)
        await gm.stop()

        await ctx.send("⏹ Stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))