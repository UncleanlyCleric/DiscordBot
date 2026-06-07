import discord
from discord.ext import commands
import wavelink
import asyncio
import logging
import random

from music.manager import MusicManager
from music.playlist_converter import PlaylistConverter
from ui.player import PlayerView

log = logging.getLogger("music")


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, MusicManager] = {}
        self.converter = PlaylistConverter()

    # =====================================================
    # PLAYER ACCESS
    # =====================================================
    def get_player(self, guild_id: int) -> MusicManager:
        if guild_id not in self.players:
            self.players[guild_id] = MusicManager(guild_id)
        return self.players[guild_id]

    # =====================================================
    # SHUFFLE
    # =====================================================
    @commands.hybrid_command(name="shuffle")
    async def shuffle(self, ctx):
        gm = self.get_player(ctx.guild.id)
        count = await gm.shuffle()
        await ctx.send(f"🔀 Shuffled {count} tracks.")

    # =====================================================
    # NOW PLAYING EMBED (CLEAN)
    # =====================================================
    def now_playing(self, track, position=0):
        title = getattr(track, "title", "Unknown Title")
        author = getattr(track, "author", "Unknown Artist")

        duration = getattr(track, "length", 0)
        pos_sec = int(position / 1000)
        dur_sec = int(duration / 1000) if duration else 0

        embed = discord.Embed(
            title="🎧 Now Playing",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Track",
            value=f"**{title}**",
            inline=False
        )

        embed.add_field(
            name="Artist",
            value=f"{author}",
            inline=True
        )

        embed.add_field(
            name="Progress",
            value=f"{pos_sec}s / {dur_sec}s",
            inline=True
        )

        uri = getattr(track, "uri", None)
        if uri:
            embed.add_field(
                name="Source",
                value=f"[Link]({uri})",
                inline=False
            )

        return embed

    # =====================================================
    # SAFE TRACK EXTRACTION (🔥 FIX CORE)
    # =====================================================
    def extract_tracks(self, results):
        """
        Normalizes ALL wavelink results into safe Playable list
        """
        if not results:
            return []

        # Playlist result
        if hasattr(results, "tracks"):
            return [
                t for t in results.tracks
                if getattr(t, "encoded", None)
            ]

        # Single result list
        if isinstance(results, list):
            return [
                t for t in results
                if getattr(t, "encoded", None)
            ]

        return []

    # =====================================================
    # PLAY COMMAND
    # =====================================================
    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):

        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = self.get_player(ctx.guild.id)

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect(cls=wavelink.Player)

        gm.player = ctx.voice_client

        queries = await self.converter.convert(query)

        if not queries:
            return await ctx.send("No results found.")

        count = 0

        for q in queries:
            try:
                results = await wavelink.Playable.search(q)
                tracks = self.extract_tracks(results)

                for t in tracks:
                    await gm.add(t)
                    count += 1

            except Exception as e:
                log.warning(f"[PLAY ERROR] {q} -> {e}")

        await ctx.send(f"🎧 Added {count} track(s)")

        # UI
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

        asyncio.create_task(self.start_progress_updater(ctx.guild.id))

    # =====================================================
    # PLAYLIST (FIXED + SAFE)
    # =====================================================
    @commands.hybrid_command(name="playlist")
    async def playlist(self, ctx, url: str, shuffle: bool = False):

        if ctx.interaction:
            await ctx.interaction.response.defer()

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        gm = self.get_player(ctx.guild.id)

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect(cls=wavelink.Player)

        gm.player = ctx.voice_client

        await ctx.send("📥 Processing playlist...")

        queries = await self.converter.convert(url)

        tracks_to_add = []

        for q in queries:
            try:
                results = await wavelink.Playable.search(q)
                tracks = self.extract_tracks(results)
                tracks_to_add.extend(tracks)

            except Exception as e:
                log.warning(f"[PLAYLIST ERROR] {q} -> {e}")

        if shuffle:
            random.shuffle(tracks_to_add)

        for t in tracks_to_add:
            await gm.add(t)

        await ctx.send(f"✅ Added {len(tracks_to_add)} tracks")

        # UI RESTORE (IMPORTANT FIX)
        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=self.now_playing(gm.current, 0)
            if gm.current
            else discord.Embed(
                title="🎧 Playlist Loaded",
                description="Queue ready",
                color=discord.Color.green()
            ),
            view=view
        )

        gm.message = msg
        gm.view = view

        asyncio.create_task(self.start_progress_updater(ctx.guild.id))

    # =====================================================
    # TRACK END HANDLER
    # =====================================================
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        player = payload.player
        if not player:
            return

        gm = self.get_player(player.guild.id)

        gm.now_playing = None
        await gm.play_next()

    # =====================================================
    # PROGRESS UPDATER
    # =====================================================
    async def start_progress_updater(self, guild_id: int):

        gm = self.get_player(guild_id)

        while gm and gm.player and gm.now_playing:
            try:
                pos = gm.player.position if gm.player else 0

                if gm.message:
                    await gm.message.edit(
                        embed=self.now_playing(gm.now_playing, pos),
                        view=gm.view
                    )

                await asyncio.sleep(5)

            except Exception:
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))