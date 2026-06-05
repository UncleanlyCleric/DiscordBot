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

    # ---------------- TRACK END ----------------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player:
            return

        gm = get_player(player.guild.id)
        await gm.play_next()

        # auto disconnect if idle
        asyncio.create_task(self.auto_disconnect(gm))

    async def auto_disconnect(self, gm: GuildMusic):
        await asyncio.sleep(60)

        if gm.is_idle() and gm.player:
            try:
                await gm.player.disconnect()
            except:
                pass
            gm.player = None

    # ---------------- EMBED ----------------
    def now_playing(self, track):
        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.blurple()
        )

        if hasattr(track, "uri") and track.uri:
            embed.add_field(name="Link", value=f"[Open]({track.uri})", inline=False)

        return embed

    # ---------------- PLAY ----------------
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        if not gm.player:
            gm.player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        query = await resolve_music(query)
        results = await wavelink.Playable.search(query)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]
        await gm.add(track)

        if not gm.current:
            await gm.play_next()

        await ctx.send(embed=self.now_playing(track))

    # ---------------- SKIP ----------------
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):
        gm = get_player(ctx.guild.id)

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # ---------------- STOP ----------------
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx: commands.Context):
        gm = get_player(ctx.guild.id)
        await gm.stop()
        await ctx.send("⏹ Stopped")

    # ---------------- RADIO ----------------
    @commands.hybrid_command(name="radio")
    async def radio(self, ctx: commands.Context, *, query: str = None):

        gm = get_player(ctx.guild.id)

        if not query:
            gm.radio_enabled = not gm.radio_enabled
            return await ctx.send(f"📻 Radio: `{gm.radio_enabled}`")

        gm.radio_enabled = True
        gm.radio_seed = query

        await ctx.send(f"📻 Radio started: `{query}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))