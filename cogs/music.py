from discord.ext import commands
import wavelink

from music.registry import get_manager


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure(self, ctx):
        if not ctx.author.voice:
            return None

        mgr = get_manager(ctx.guild.id)
        player = await mgr.connect(ctx.author.voice.channel)

        return mgr, player

    # ---------------- PLAY ----------------
    @commands.hybrid_command()
    async def play(self, ctx, *, query: str):
        result = await self.ensure(ctx)
        if not result:
            return await ctx.send("Join a voice channel first.")

        mgr, player = result

        tracks = await wavelink.Playable.search(query)
        if not tracks:
            return await ctx.send("No results.")

        track = tracks[0]

        await mgr.add(track)

        await ctx.send(f"Queued: **{track.title}**")

        if not player.playing:
            await mgr.play_next()

    # ---------------- SKIP ----------------
    @commands.hybrid_command()
    async def skip(self, ctx):
        mgr = get_manager(ctx.guild.id)
        await mgr.skip()
        await mgr.play_next()
        await ctx.send("Skipped.")

    # ---------------- STOP ----------------
    @commands.hybrid_command()
    async def stop(self, ctx):
        mgr = get_manager(ctx.guild.id)
        await mgr.stop()
        await ctx.send("Stopped.")


async def setup(bot):
    await bot.add_cog(Music(bot))