import discord
from discord.ext import commands
import wavelink
import asyncio
import logging

from music.manager import MusicManager
from music.playlist_converter import PlaylistConverter
from ui.player import PlayerView

log = logging.getLogger("music")


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, MusicManager] = {}
        self.converter = PlaylistConverter()

        # prevent duplicate updater loops
        self.progress_tasks: dict[int, asyncio.Task] = {}

    # ---------------- PLAYER ACCESS ----------------
    def get_player(self, guild_id: int) -> MusicManager:
        if guild_id not in self.players:
            self.players[guild_id] = MusicManager(guild_id)
        return self.players[guild_id]

    # ---------------- EMBED ----------------
    def now_playing(self, track, position=0):
        title = getattr(track, "title", "Unknown Title")
        author = getattr(track, "author", "Unknown Artist")
        duration = getattr(track, "length", 0)

        progress = f"{int(position/1000)}s / {int(duration/1000)}s"

        embed = discord.Embed(
            title="🎧 Now Playing",
            description=f"🎵 **{title}**\n🎤 **{author}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="⏱ Progress",
            value=progress,
            inline=True
        )

        uri = getattr(track, "uri", None)
        if uri:
            embed.add_field(
                name="🔗 Source",
                value=f"[Open Track]({uri})",
                inline=False
            )

        return embed

    # ---------------- PLAY ----------------
    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):

        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = self.get_player(ctx.guild.id)

        if not gm.player:
            await gm.connect(ctx.author.voice.channel)

        queries = await self.converter.convert(query)

        if not queries:
            return await ctx.send("No results found.")

        count = 0

        for q in queries:

            try:
                # allow youtube URLs
                if "youtube.com" in q or "youtu.be" in q:
                    results = await wavelink.Playable.search(q)
                else:
                    results = await wavelink.Playable.search(q)

                if not results:
                    continue

                track = results[0]

                await gm.add(track)
                count += 1

            except Exception as e:
                log.warning(f"[PLAY ERROR] {q} -> {e}")

        await ctx.send(f"🎧 Added {count} track(s)")

        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=self.now_playing(gm.now_playing, 0)
            if gm.now_playing else discord.Embed(
                title="🎧 Player Ready",
                description="Queue started",
                color=discord.Color.green()
            ),
            view=view
        )

        gm.message = msg
        gm.view = view

        if (
            ctx.guild.id not in self.progress_tasks
            or self.progress_tasks[ctx.guild.id].done()
        ):
            self.progress_tasks[ctx.guild.id] = asyncio.create_task(
                self.start_progress_updater(ctx.guild.id)
            )

    # ---------------- PLAYLIST ----------------
    @commands.hybrid_command(name="playlist")
    async def playlist(self, ctx, url: str):

        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = self.get_player(ctx.guild.id)

        if not gm.player:
            await gm.connect(ctx.author.voice.channel)

        await ctx.send("📥 Processing playlist...")

        queries = await self.converter.convert(url)

        count = 0

        for q in queries:

            try:
                results = await wavelink.Playable.search(q)

                if not results:
                    continue

                track = results[0]

                await gm.add(track)
                count += 1

            except Exception as e:
                log.warning(f"[PLAYLIST ERROR] {q} -> {e}")

        await ctx.send(f"✅ Added {count} tracks")

    # ---------------- TRACK END ----------------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):

        player = payload.player

        if not player or not player.guild:
            return

        gm = self.get_player(player.guild.id)

        gm.now_playing = None

        try:
            await gm.play_next()
        except Exception as e:
            log.error(f"Track end error: {e}")

    # ---------------- TRACK ERROR ----------------
    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload):

        player = payload.player

        if not player or not player.guild:
            return

        gm = self.get_player(player.guild.id)

        gm.now_playing = None

        try:
            await gm.play_next()
        except Exception as e:
            log.error(f"Track exception error: {e}")

    # ---------------- UI UPDATER ----------------
    async def start_progress_updater(self, guild_id: int):

        gm = self.get_player(guild_id)

        while True:

            try:

                if (
                    not gm.player
                    or not gm.now_playing
                    or not gm.message
                ):
                    await asyncio.sleep(5)
                    continue

                pos = gm.player.position

                await gm.message.edit(
                    embed=self.now_playing(
                        gm.now_playing,
                        pos
                    ),
                    view=gm.view
                )

                await asyncio.sleep(5)

            except Exception:
                break

        self.progress_tasks.pop(guild_id, None)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))