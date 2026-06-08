import asyncio
import logging

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
from services.music.persistence import music_persistence
from services.music.controller import music_controller


COGS = [
    "cogs.admin",
    "cogs.help",
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
    # STARTUP SEQUENCE
    # =====================================================

    async def setup_hook(self):
        """
        Boot order:

        1. DB migrations
        2. DB connect
        3. Lavalink connect
        4. Load cogs
        5. Slash sync
        6. Restore music state
        7. Restart runtime
        """

        # -------------------------
        # 1. DATABASE MIGRATIONS
        # -------------------------
        logging.info("[BOOT] Running migrations...")
        await migration_runner.run()

        # -------------------------
        # 2. DATABASE CONNECT
        # -------------------------
        logging.info("[BOOT] Connecting DB...")
        await db.connect()

        # -------------------------
        # 3. LAVALINK CONNECT
        # -------------------------
        logging.info("[LAVALINK] Connecting node...")

        import os

        uri = os.getenv("LAVALINK_URI", "http://localhost:2333")
        password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

        nodes = [
            wavelink.Node(
                uri=uri,
                password=password
            )
        ]

        await wavelink.Pool.connect(
            client=self,
            nodes=nodes
        )

        # -------------------------
        # 4. LOAD COGS (WITH AUDIT LOGGING)
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
        # 5. SLASH COMMAND SYNC
        # -------------------------
        try:
            synced = await self.tree.sync()
            logging.info("[CMD] Synced %s commands", len(synced))
        except Exception:
            logging.exception("[CMD] Sync failed")

        # -------------------------
        # 6. RESTORE MUSIC STATE
        # -------------------------
        logging.info("[MUSIC] Restoring state...")

        for player in music_manager.get_all():
            try:
                tracks = await music_persistence.load_queue(player.guild_id)

                for track in tracks:
                    player.queue.add(track)

            except Exception:
                logging.exception(
                    "[MUSIC] Failed restore guild %s",
                    player.guild_id
                )

        # -------------------------
        # 7. RESTART RUNTIME LOOPS
        # -------------------------
        logging.info("[MUSIC] Restarting runtime...")
        await music_runtime.restart_all()

    # =====================================================
    # READY EVENT
    # =====================================================

    async def on_ready(self):
        logging.info(
            "[READY] Logged in as %s (%s)",
            self.user,
            self.user.id
        )

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
    # LAVALINK EVENT HANDLING
    # =====================================================

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """
        Fired when a track finishes playing.
        Advances queue safely.
        """

        guild_id = payload.player.guild.id
        player = music_manager.get_player(guild_id)

        player.skip()

    # =====================================================
    # CLEAN SHUTDOWN
    # =====================================================

    async def close(self):
        logging.info("[SHUTDOWN] Stopping bot...")

        # stop music loops
        for player in music_manager.get_all():
            music_controller.stop_loop(player.guild_id)

        await db.close()

        await super().close()


# =========================================================
# MAIN ENTRY
# =========================================================

async def main():
    setup_logging()

    bot = DiscordBot()

    token = config.discord_token

    if not token:
        raise RuntimeError("DISCORD_TOKEN missing")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())