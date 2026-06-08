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
from services.music.runtime import music_runtime
from services.music.controller import music_controller


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

    # =====================================================
    # BOOT
    # =====================================================
    async def setup_hook(self):
        logging.info("[BOOT] Running migrations...")
        await migration_runner.run()

        logging.info("[BOOT] Connecting DB...")
        await db.connect()

        # =====================================================
        # LAVALINK
        # =====================================================
        logging.info("[LAVALINK] Connecting node...")

        nodes = [
            wavelink.Node(
                uri=config.lavalink_uri,
                password=config.lavalink_password
            )
        ]

        await wavelink.Pool.connect(
            client=self,
            nodes=nodes
        )

        # wait for node
        for _ in range(20):
            if wavelink.Pool.nodes:
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError("Lavalink node failed to connect")

        logging.info("[LAVALINK] Node is ready.")

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
        # SYNC
        # =====================================================
        try:
            synced = await self.tree.sync()
            logging.info("[CMD] Synced %s commands", len(synced))
        except Exception:
            logging.exception("[CMD] Sync failed")

        # =====================================================
        # RESTORE MUSIC STATE
        # =====================================================
        logging.info("[MUSIC] Restoring state...")

        await asyncio.sleep(1)

        for player in music_manager.get_all():
            try:
                tracks = await music_runtime.load_queue(player.guild_id)
                for t in tracks:
                    player.queue.add(t)
            except Exception:
                logging.exception("[MUSIC] Restore failed %s", player.guild_id)

        await music_runtime.restart_all()

    # =====================================================
    # READY
    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s (%s)", self.user, self.user.id)

    # =====================================================
    # COMMAND AUDIT
    # =====================================================
    async def on_app_command_completion(self, interaction, command):
        audit.command_called(
            user_id=interaction.user.id,
            guild_id=interaction.guild_id or 0,
            command=command.qualified_name
        )

    async def on_app_command_error(self, interaction, error: Exception):
        audit.command_failed(
            command=getattr(interaction.command, "qualified_name", "unknown"),
            error=error
        )

    # =====================================================
    # LAVALINK READY
    # =====================================================
    async def on_wavelink_node_ready(self, payload):
        logging.info("[LAVALINK] Node fully ready: %s", payload.node.identifier)

    # =====================================================
    # TRACK END (FIXED)
    # =====================================================
    async def on_wavelink_track_end(self, payload):
        """
        DO NOT mutate state here anymore.
        Controller handles queue progression.
        """

        if not payload.player:
            return

        guild = getattr(payload.player, "guild", None)
        if not guild:
            return

        guild_id = guild.id

        # Let controller decide next track
        await music_controller.play_next(guild_id)

    # =====================================================
    # SHUTDOWN
    # =====================================================
    async def close(self):
        logging.info("[SHUTDOWN] Cleaning up bot...")

        for player in music_manager.get_all():
            music_controller.stop_loop(player.guild_id)

        try:
            await music_runtime.shutdown()
        except Exception:
            pass

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
    setup_logging()

    bot = DiscordBot()

    token = config.discord_token
    if not token:
        raise RuntimeError("DISCORD_TOKEN missing")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())