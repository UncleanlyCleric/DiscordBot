import discord
from discord.ext import commands
import wavelink
import asyncio
import logging

from music.manager import MusicManager
from music.utils import create_bar
from ui.player import PlayerView

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

    # ---------------- TRACK END ----------------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        try:
            gm = get_player(payload.player.guild.id)
            gm.player = payload.player
            await gm.play_next()
        except Exception as e:
            log.error(f"track_end error: {e}")

    # ---------------- PRO NOW PLAYING ----------------
    def now_playing(self, track, position=0):
        duration = getattr(track, "length", 0)

        bar = create_bar(position, duration)

        embed = discord.Embed(
            title="🎧 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )

        embed.add_field(name="Progress", value=f"`{bar}`", inline=False)
        embed.add_field(
            name="Time",
            value=f"{int(position/1000)}s / {int(duration/1000)}s",
            inline=True
        )

        return embed

    # ---------------- LIVE UPDATER ----------------
    async def start_progress_updater(self, guild_id: int):
        gm = get_player(guild_id)

        while gm and gm.player and gm.now_playing:
            try:
                pos = gm.player.position if gm.player else 0

                embed = self.now_playing(gm.now_playing, pos)

                if gm.message:
                    await gm.message.edit(embed=embed, view=gm.view)

                await asyncio.sleep(5)

            except Exception:
                break

    # ---------------- PLAY ----------------
    @commands.hybrid_command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):

        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = get_player(ctx.guild.id)

        try:
            voice = ctx.voice_client

            if not voice:
                voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            else:
                if voice.channel != ctx.author.voice.channel:
                    await voice.move_to(ctx.author.voice.channel)

        except Exception as e:
            return await ctx.send(f"Voice error: {e}")

        gm.player = voice

        results = None

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

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        await gm.add(track)

        if not gm.now_playing:
            await gm.play_next()

        # UI
        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=self.now_playing(track, 0),
            view=view
        )

        gm.message = msg
        gm.view = view

        asyncio.create_task(self.start_progress_updater(ctx.guild.id))

    # ---------------- VOTE SKIP ----------------
    @commands.hybrid_command(name="voteskip")
    async def voteskip(self, ctx):
        gm = get_player(ctx.guild.id)

        if not gm.player:
            return await ctx.send("Nothing playing.")

        if not ctx.author.voice:
            return await ctx.send("Join voice first.")

        gm.skip_votes.add(ctx.author.id)

        members = len([m for m in ctx.author.voice.channel.members if not m.bot])
        needed = max(1, members // 2 + 1)

        if len(gm.skip_votes) >= needed:
            await gm.player.stop()
            gm.skip_votes.clear()
            return await ctx.send("⏭ Vote skip passed!")

        await ctx.send(f"🗳 Votes: {len(gm.skip_votes)}/{needed}")

    # ---------------- AUTOPLAY ----------------
    @commands.hybrid_command(name="autoplay")
    async def autoplay(self, ctx, query: str):
        gm = get_player(ctx.guild.id)

        gm.radio_enabled = True
        gm.radio_seed = query

        await ctx.send(f"📻 Autoplay enabled: **{query}**")

    # ---------------- QUEUE ----------------
    @commands.hybrid_command(name="queue")
    async def queue(self, ctx):
        gm = get_player(ctx.guild.id)

        if gm.queue.empty() and not gm.now_playing:
            return await ctx.send("Queue is empty.")

        items = list(gm.queue._queue)[:10]

        desc = ""

        if gm.now_playing:
            desc += f"🎧 Now: **{gm.now_playing.title}**\n\n"

        for i, t in enumerate(items, 1):
            desc += f"{i}. {t.title}\n"

        await ctx.send(
            embed=discord.Embed(
                title="📜 Queue",
                description=desc,
                color=discord.Color.blurple()
            )
        )

    # ---------------- SKIP ----------------
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx):
        gm = get_player(ctx.guild.id)

        if gm.player:
            await gm.player.stop()

        await ctx.send("⏭ Skipped")

    # ---------------- STOP ----------------
    @commands.hybrid_command(name="stop")
    async def stop(self, ctx):
        gm = get_player(ctx.guild.id)

        await gm.stop()
        await ctx.send("⏹ Stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))