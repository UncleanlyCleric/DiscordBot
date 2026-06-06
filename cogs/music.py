import discord
from discord.ext import commands
import wavelink
import asyncio
import logging

from music.manager import MusicManager
from music.utils import create_bar
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

    # ---------------- TRACK END ----------------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        try:
            gm = self.get_player(payload.player.guild.id)
            gm.player = payload.player
            await gm.play_next()
        except Exception as e:
            log.error(f"track_end error: {e}")

    # ---------------- EMBED ----------------
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

    # ---------------- PLAYLIST COMMAND ----------------
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

        await ctx.send("📥 Converting playlist...")

        queries = await self.converter.convert(url)

        if not queries:
            return await ctx.send("❌ Could not extract playlist.")

        count = 0

        for q in queries:
            try:
                results = await wavelink.Playable.search(f"ytmsearch:{q}")

                if results:
                    track = results[0]
                    await gm.add(track)
                    count += 1

                    # prevents rate spikes + improves stability
                    await asyncio.sleep(0.2)

            except Exception as e:
                log.error(f"playlist search error: {e}")
                continue

        await ctx.send(f"✅ Added {count} tracks to queue")

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

        results = await wavelink.Playable.search(f"ytmsearch:{query}")

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        await gm.add(track)

        view = PlayerView(self.bot, ctx.guild.id)

        msg = await ctx.send(
            embed=self.now_playing(track, 0),
            view=view
        )

        gm.message = msg
        gm.view = view

        asyncio.create_task(self.start_progress_updater(ctx.guild.id))

    # ---------------- UI UPDATER ----------------
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

            except Exception as e:
                log.error(f"UI update error: {e}")
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))