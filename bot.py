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


# =====================================================
# SAFETY: ensure module imports work in Docker/local
# =====================================================
sys.path.append(str(Path(__file__).resolve().parent))


# =====================================================
# ACTIVE COGS ONLY (FIXED)
# =====================================================
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
    # BOOT SEQUENCE
    # =====================================================
    async def setup_hook(self):
        logging.info("[BOOT] Running migrations...")
        await migration_runner.run()

        logging.info("[BOOT] Connecting DB...")
        await db.connect()

        # -------------------------
        # LAVALINK
        # -------------------------
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

        # -------------------------
        # COG LOAD
        # -------------------------
        for cog in COGS:
            try:
                await self.load_extension(cog)
                audit.cog_loaded(cog)
                logging.info("[COG] Loaded %s", cog)

            except Exception as e:
                audit.cog_failed(cog, e)
                logging.exception("[COG] Failed %s", cog)

        # -------------------------
        # SYNC COMMANDS
        # -------------------------
        try:
            synced = await self.tree.sync()
            logging.info("[CMD] Synced %s commands", len(synced))
        except Exception:
            logging.exception("[CMD] Sync failed")

        # -------------------------
        # MUSIC RESTORE
        # -------------------------
        logging.info("[MUSIC] Restoring state...")

        await asyncio.sleep(1)  # allow wavelink + gateway to stabilize

        for player in music_manager.get_all():
            try:
                tracks = await music_runtime.load_queue(player.guild_id)
                for t in tracks:
                    player.queue.add(t)
            except Exception:
                logging.exception("[MUSIC] Restore failed %s", player.guild_id)

        await music_runtime.restart_all()

    # =====================================================
    # READY EVENT
    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s (%s)", self.user, self.user.id)

    # =====================================================
    # COMMAND AUDIT LOGGING
    # =====================================================
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        audit.command_called(
            user_id=interaction.user.id,
            guild_id=interaction.guild_id or 0,
            command=command.qualified_name
        )

    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception):
        audit.command_failed(
            command=getattr(interaction.command, "qualified_name", "unknown"),
            error=error
        )

    # =====================================================
    # LAVALINK EVENTS
    # =====================================================
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        guild_id = payload.player.guild.id
        player = music_manager.get_player(guild_id)
        player.skip()

    # =====================================================
    # CLEAN SHUTDOWN (FIXED ORDER)
    # =====================================================
    async def close(self):
        logging.info("[SHUTDOWN] Cleaning up bot...")

        # 1. stop music loops
        for player in music_manager.get_all():
            music_controller.stop_loop(player.guild_id)

        # 2. stop runtime systems
        try:
            await music_runtime.shutdown()
        except Exception:
            pass

        # 3. disconnect Lavalink BEFORE Discord session closes
        try:
            await wavelink.Pool.disconnect()
        except Exception:
            pass

        # 4. close database
        try:
            await db.close()
        except Exception:
            pass

        await super().close()


# =====================================================
# ENTRYPOINT
# =====================================================
async def main():
    setup_logging()

    bot = DiscordBot()

    token = config.discord_token
    if not token:
        raise RuntimeError("DISCORD_TOKEN missing")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())