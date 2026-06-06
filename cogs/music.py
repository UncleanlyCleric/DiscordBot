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
    # TRACK END EVENT
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
    # PLAY COMMAND
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        # Slash support
        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        # =====================================================
        # SAFE VOICE CONNECT
        # =====================================================
        try:
            voice = ctx.voice_client

            if not voice:
                log.info("[VOICE] connecting...")
                voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                log.info("[VOICE] connected")
            else:
                # move if needed instead of reconnecting
                if voice.channel != ctx.author.voice.channel:
                    await voice.move_to(ctx.author.voice.channel)
                log.info("[VOICE] reused existing connection")

        except discord.ClientException:
            voice = ctx.voice_client
        except Exception as e:
            log.error(f"[VOICE] connect error: {e}")
            return await ctx.send(f"❌ Voice error: {e}")

        gm.player = voice

        # =====================================================
        # SAFE SEARCH (FIXED LAVALINK / YOUTUBE ISSUE)
        # =====================================================
        try:
            log.info(f"[SEARCH] {query}")

            results = None

            # FORCE SAFE SOURCES (prevents base.js crash)
            for q in (f"ytsearch:{query}", f"scsearch:{query}"):

                try:
                    results = await asyncio.wait_for(
                        wavelink.Playable.search(q),
                        timeout=10
                    )

                    if results:
                        break

                except Exception as e:
                    log.warning(f"[SEARCH FAIL] {q}: {e}")

        except asyncio.TimeoutError:
            return await ctx.send("❌ Search timed out.")
        except Exception as e:
            log.error(f"[SEARCH] error: {e}")
            return await ctx.send("❌ Search failed.")

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        log.info(f"[QUEUE] {track.title}")

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

        try:
            vc = await ctx.author.voice.channel.connect()
            await ctx.send("Connected successfully")

            await asyncio.sleep(2)
            await vc.disconnect()

        except discord.ClientException:
            await ctx.send("Already connected somewhere.")
        except Exception as e:
            log.error(f"voicetest error: {e}")
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