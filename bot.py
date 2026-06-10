import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands
import wavelink

from core.logger import setup_logging
from core.config import config
from core.database import db
from core.audit_logger import audit
from database.migrations import migration_runner

from services.music.manager import music_manager
from services.music.player_engine import engine
from services.music.player_message_manager import player_message_manager
from services.music.ui.music_player_view import MusicPlayerView


sys.path.append(str(Path(__file__).resolve().parent))


COGS = [
    "cogs.quotes",
    "cogs.dice",
    "cogs.markov",
    "cogs.music",
]


class DiscordBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

        self.dev_guild_id = getattr(config, "dev_guild_id", None)

    # =====================================================
    async def setup_hook(self):

        setup_logging()

        logging.info("[BOOT] Running migrations...")
        await migration_runner.run()

        logging.info("[BOOT] Connecting DB...")
        await db.connect()

        # =====================================================
        # LAVALINK
        # =====================================================
        logging.info("[LAVALINK] Connecting node...")

        node = wavelink.Node(
            uri=config.lavalink_uri,
            password=config.lavalink_password
        )

        await wavelink.Pool.connect(
            client=self,
            nodes=[node]
        )

        # wait for node
        for _ in range(20):
            if wavelink.Pool.nodes:
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError("Lavalink node failed to connect")

        logging.info("[LAVALINK] Node ready")

        # =====================================================
        # COGS
        # =====================================================
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logging.info("[COG] Loaded %s", cog)
            except Exception:
                logging.exception("[COG] Failed %s", cog)

        # =====================================================
        # PERSISTENT UI VIEW
        # =====================================================
        self.add_view(MusicPlayerView())

        # =====================================================
        # START PROGRESS LOOP
        # =====================================================
        self.loop.create_task(self.progress_updater())

    # =====================================================
    async def progress_updater(self):
        await self.wait_until_ready()

        while not self.is_closed():
            try:
                for guild in self.guilds:
                    await player_message_manager.update(guild)
            except Exception:
                pass

            await asyncio.sleep(5)

    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s", self.user)

    # =====================================================
    # ❌ FIXED: NO BROKEN HANDLER CALL
    # =====================================================
    async def on_wavelink_track_end(self, payload):
        try:
            player = payload.player
            state = music_manager.get_player(player.guild.id)

            queue = state.queue.all()

            if not queue:
                await player_message_manager.update(player.guild)
                return

            next_track = state.queue.pop()

            await player.play(next_track)

            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception("[MUSIC] track_end failed safely")

    # =====================================================
    async def close(self):
        try:
            await wavelink.Pool.disconnect()
        except Exception:
            pass

        try:
            await db.close()
        except Exception:
            pass

        await super().close()


async def main():
    bot = DiscordBot()

    token = config.discord_token
    if not token:
        raise RuntimeError("DISCORD_TOKEN missing")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())