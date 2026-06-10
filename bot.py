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
    # SETUP
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

        for _ in range(20):
            if wavelink.Pool.nodes:
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError("Lavalink failed to connect")

        logging.info("[LAVALINK] Ready.")

        # =====================================================
        # COGS
        # =====================================================
        for cog in COGS:
            try:
                await self.load_extension(cog)

                audit.cog_loaded(cog)

                logging.info(
                    "[COG] Loaded %s",
                    cog
                )

            except Exception as e:

                audit.cog_failed(cog, e)

                logging.exception(
                    "[COG] Failed %s",
                    cog
                )

        # =====================================================
        # PERSISTENT UI
        # =====================================================
        self.add_view(MusicPlayerView())

        # =====================================================
        # COMMAND SYNC
        # =====================================================
        try:

            synced = await self.tree.sync()

            logging.info(
                "[CMD] Synced %s commands",
                len(synced)
            )

        except Exception:
            logging.exception("[CMD] Sync failed")

    # =====================================================
    # READY
    # =====================================================
    async def on_ready(self):

        logging.info(
            "[READY] Logged in as %s",
            self.user
        )

    # =====================================================
    # GENERIC WAVELINK EVENT LISTENER
    # =====================================================
    async def on_wavelink_event(self, payload):

        try:

            logging.info(
                "[WAVELINK_EVENT] %s",
                payload.__class__.__name__
            )

            from services.music.player_engine import engine

            if isinstance(
                payload,
                wavelink.TrackEndEventPayload
            ):

                logging.info(
                    "[TRACK_END] reason=%s guild=%s",
                    payload.reason,
                    payload.player.guild.id
                )

                if str(payload.reason).lower() == "finished":

                    logging.info(
                        "[TRACK_END] advancing queue"
                    )

                    await engine.handle_track_end(
                        payload.player
                    )

        except Exception:
            logging.exception(
                "[WAVELINK_EVENT] failed"
            )

    # =====================================================
    # TRACK END
    # =====================================================
    async def on_wavelink_track_end(
        self,
        payload: wavelink.TrackEndEventPayload
    ):
        """
        Backup listener.
        """

        try:

            logging.info(
                "[TRACK_END_DIRECT] reason=%s guild=%s",
                payload.reason,
                payload.player.guild.id
            )

            from services.music.player_engine import engine

            if str(payload.reason).lower() != "finished":

                logging.info(
                    "[TRACK_END_DIRECT] ignored reason=%s",
                    payload.reason
                )

                return

            logging.info(
                "[TRACK_END_DIRECT] advancing queue"
            )

            await engine.handle_track_end(
                payload.player
            )

        except Exception:
            logging.exception(
                "[MUSIC] track_end failed"
            )

    # =====================================================
    # NODE READY
    # =====================================================
    async def on_wavelink_node_ready(
        self,
        payload
    ):
        logging.info(
            "[LAVALINK] Node ready: %s",
            payload.node.identifier
        )

    # =====================================================
    # SHUTDOWN
    # =====================================================
    async def close(self):

        logging.info(
            "[SHUTDOWN] Cleaning up..."
        )

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
        raise RuntimeError(
            "Missing DISCORD_TOKEN"
        )

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())