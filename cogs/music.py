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

    # ---------------- PLAYER ----------------
    def get_player(self, guild_id: int) -> MusicManager:
        if guild_id not in self.players:
            self.players[guild_id] = MusicManager(guild_id)
        return self.players[guild_id]

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
            voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        gm.player = voice

        await ctx.send("📥 Processing playlist...")

        queries = await self.converter.convert(url)

        if not queries:
            return await ctx.send("❌ No valid tracks found.")

        count = 0

        for q in queries:

            # 🚨 HARD SAFETY: NEVER allow URLs
            if "http" in q:
                continue

            try:
                results = await wavelink.Playable.search(q)

                if not results:
                    continue

                await gm.add(results[0])
                count += 1

            except Exception as e:
                log.warning(f"playlist item failed: {q} -> {e}")
                continue

        await ctx.send(f"✅ Added {count} tracks")

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
            voice = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        gm.player = voice

        # 🚨 FIX: no ytmsearch prefix
        results = await wavelink.Playable.search(query)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        await gm.add(track)

        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=discord.Embed(
                title="🎧 Now Playing",
                description=track.title,
                color=discord.Color.green()
            ),
            view=view
        )

        gm.message = msg
        gm.view = view

        asyncio.create_task(self.start_progress_updater(ctx.guild.id))

    # ---------------- UI ----------------
    async def start_progress_updater(self, guild_id: int):
        gm = self.get_player(guild_id)

        while gm and gm.player and gm.now_playing:
            try:
                pos = gm.player.position if gm.player else 0

                if gm.message:
                    await gm.message.edit(
                        embed=discord.Embed(
                            title="🎧 Now Playing",
                            description=getattr(gm.now_playing, "title", "Unknown"),
                            color=discord.Color.green()
                        ),
                        view=gm.view
                    )

                await asyncio.sleep(5)

            except Exception:
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))