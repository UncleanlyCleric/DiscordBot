import discord
from discord.ext import commands
import wavelink
import asyncio
import logging

from music.manager import MusicManager


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
    # PLAY COMMAND (FIXED VOICE TIMEOUT)
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        # =========================
        # SLASH SAFETY
        # =========================
        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # =====================================================
        # 🔥 FIX: HARD RESET STUCK VOICE SESSION
        # =====================================================
        voice = ctx.voice_client

        if voice:
            try:
                log.info("[VOICE] forcing cleanup of old session")
                await voice.disconnect(force=True)
                await asyncio.sleep(1)  # allow Discord to fully clear state
            except Exception as e:
                log.warning(f"[VOICE] cleanup warning: {e}")

        # =====================================================
        # 🔥 FIX: SAFE FRESH CONNECT (prevents 30s timeout)
        # =====================================================
        try:
            log.info("[VOICE] connecting fresh")

            voice = await asyncio.wait_for(
                ctx.author.voice.channel.connect(cls=wavelink.Player),
                timeout=10
            )

            log.info("[VOICE] connected successfully")

        except asyncio.TimeoutError:
            log.error("[VOICE] TIMEOUT")
            return await ctx.send("❌ Voice connection timed out.")
        except Exception as e:
            log.error(f"[VOICE] ERROR: {e}")
            return await ctx.send(f"❌ Voice error: {e}")

        gm.player = voice

        # =====================================================
        # RESOLVE QUERY
        # =====================================================
        try:
            log.info(f"[SEARCH] query: {query}")

            query = await resolve_music(query)

            results = await asyncio.wait_for(
                wavelink.Playable.search(query),
                timeout=10
            )

        except asyncio.TimeoutError:
            return await ctx.send("❌ Search timed out.")
        except Exception as e:
            log.error(f"[SEARCH] ERROR: {e}")
            return await ctx.send("❌ Search failed.")

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        log.info(f"[QUEUE] adding: {track.title}")

        await gm.add(track)

        if not gm.now_playing:
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

    # =====================================================
    # VOICE TEST
    # =====================================================
    @commands.command()
    async def voicetest(self, ctx):

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        log.info("VOICE TEST START")
        log.info("BEFORE CONNECT")

        try:
            vc = await ctx.author.voice.channel.connect()

            log.info("AFTER CONNECT")

            await ctx.send("Connected successfully")

            await asyncio.sleep(2)

            await vc.disconnect()

            log.info("VOICE TEST END")

        except Exception as e:
            log.error(f"VOICE TEST ERROR: {e}")
            await ctx.send(f"Voice test failed: {e}")

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