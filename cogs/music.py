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

    # ---------------- PLAYER ACCESS ----------------
    def get_player(self, guild_id: int) -> MusicManager:
        if guild_id not in self.players:
            self.players[guild_id] = MusicManager(guild_id)
        return self.players[guild_id]

    # ---------------- EMBED (UPGRADED UI) ----------------
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

        voice = ctx.voice_client
        if not voice:
            voice = await ctx.author.voice.channel.connect(
                cls=wavelink.Player
            )

        gm.player = voice

        queries = await self.converter.convert(query)

        if not queries:
            return await ctx.send("No results found.")

        count = 0

        for q in queries:

            if not isinstance(q, str) or "http" in q:
                continue

            try:
                print("ABOUT TO SEARCH:", q)
                results = await wavelink.Playable.search(q)
                print("SEARCH FINISHED")

                print("================================")
                print("SEARCH:", q)
                print("RESULT TYPE:", type(results))
                print("RESULT COUNT:", len(results) if results else 0)

                if results:
                    track = results[0]

                    print("TITLE:", getattr(track, "title", None))
                    print("AUTHOR:", getattr(track, "author", None))
                    print("IDENTIFIER:", getattr(track, "identifier", None))
                    print("ENCODED:", getattr(track, "encoded", None))

                print("================================")

                if not results:
                    continue

                await gm.add(results[0])
                count += 1

            except Exception as e:
                log.warning(f"[PLAY ERROR] {q} -> {e}")

        await ctx.send(f"🎧 Added {count} track(s)")

        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=self.now_playing(gm.now_playing, 0)
            if gm.now_playing
            else discord.Embed(
                title="🎧 Player Ready",
                description="Queue started",
                color=discord.Color.green()
            ),
            view=view
        )

        gm.message = msg
        gm.view = view

        asyncio.create_task(
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

        voice = ctx.voice_client
        if not voice:
            voice = await ctx.author.voice.channel.connect(
                cls=wavelink.Player
            )

        gm.player = voice

        await ctx.send("📥 Processing playlist...")

        queries = await self.converter.convert(url)

        if not queries:
            return await ctx.send("No tracks found.")

        count = 0

        for q in queries:

            if not isinstance(q, str) or "http" in q:
                continue

            try:
                results = await wavelink.Playable.search(q)

                print("================================")
                print("SEARCH:", q)
                print("RESULT TYPE:", type(results))
                print("RESULT COUNT:", len(results) if results else 0)

                if results:
                    track = results[0]

                    print("TITLE:", getattr(track, "title", None))
                    print("AUTHOR:", getattr(track, "author", None))
                    print("IDENTIFIER:", getattr(track, "identifier", None))
                    print("ENCODED:", getattr(track, "encoded", None))

                print("================================")

                if not results:
                    continue

                await gm.add(results[0])
                count += 1

            except Exception as e:
                log.warning(f"[PLAYLIST ERROR] {q} -> {e}")

        await ctx.send(f"✅ Added {count} tracks")

    # ---------------- UI UPDATER ----------------
    async def start_progress_updater(self, guild_id: int):
        gm = self.get_player(guild_id)

        while gm and gm.player and gm.now_playing:
            try:
                pos = gm.player.position if gm.player else 0

                if gm.message:
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))