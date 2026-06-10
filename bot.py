import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

import wavelink

from services.music.ui.music_player_view import MusicPlayerView
from core.logger import setup_logging
from core.config import config
from core.database import db
from core.audit_logger import audit
from database.migrations import migration_runner

from services.music.manager import music_manager
from services.music.player_engine import engine
from services.music.player_message_manager import player_message_manager


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
        # LAVALINK NODE
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

        logging.info("[LAVALINK] Node ready")

        # =====================================================
        # COGS
        # =====================================================
        for cog in COGS:
            try:
                await self.load_extension(cog)
                audit.cog_loaded(cog)
                logging.info("[COG] Loaded %s", cog)
            except Exception as e:
                audit.cog_failed(cog, e)
                logging.exception("[COG] Failed %s", cog)

        # =====================================================
        # PERSISTENT UI VIEW
        # =====================================================
        self.add_view(MusicPlayerView())

        # =====================================================
        # COMMAND SYNC
        # =====================================================
        try:
            global_synced = await self.tree.sync()
            logging.info("[CMD] Global synced %s commands", len(global_synced))

            guild_id = self.dev_guild_id

            if not guild_id and self.guilds:
                guild_id = self.guilds[0].id

            if guild_id:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                dev_synced = await self.tree.sync(guild=guild)

                logging.info("[CMD] Dev synced %s commands", len(dev_synced))

        except Exception:
            logging.exception("[CMD] Sync failed")

    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s", self.user)

    # =====================================================
    # 🚨 FIXED: SAFE TRACK END HANDLER
    # =====================================================
    async def on_wavelink_track_end(self, payload):
        """
        Replaces broken engine.handle_track_end()
        """

        try:
            player = payload.player
            guild_id = player.guild.id

            state = music_manager.get_player(guild_id)

            logging.info("[MUSIC] track_end guild=%s", guild_id)

            queue = state.queue.all()

            if not queue:
                logging.info("[MUSIC] queue empty")
                return

            next_track = state.queue.pop()

            logging.info("[MUSIC] next=%s", next_track.title)

            await player.play(next_track)

            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception("[MUSIC] track_end failed safely")

    # =====================================================
    async def on_wavelink_node_ready(self, payload):
        logging.info("[LAVALINK] Node ready: %s", payload.node.identifier)

    # =====================================================
    async def close(self):
        logging.info("[SHUTDOWN] closing bot...")

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