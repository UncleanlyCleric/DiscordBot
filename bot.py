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
    # BOOT
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

        # WAIT FOR NODE SAFELY
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

        # persistent UI view
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
                logging.info("[CMD] Auto-selected dev guild: %s", guild_id)

            if guild_id:
                guild = discord.Object(id=guild_id)

                self.tree.copy_global_to(guild=guild)
                dev_synced = await self.tree.sync(guild=guild)

                logging.info(
                    "[CMD] Dev guild synced %s commands (guild=%s)",
                    len(dev_synced),
                    guild_id
                )
            else:
                logging.warning("[CMD] No dev guild available")

        except Exception:
            logging.exception("[CMD] Sync failed")

        # =====================================================
        # MUSIC RESTORE (SAFE)
        # =====================================================
        logging.info("[MUSIC] Restoring state...")

        await asyncio.sleep(1)

        try:
            for player in list(music_manager.get_all()):
                try:
                    tracks = player.queue.all()
                    player.queue.clear()

                    for t in tracks:
                        player.queue.add(t)

                except Exception:
                    logging.exception(
                        "[MUSIC] Restore failed %s",
                        getattr(player, "guild_id", "unknown")
                    )

        except Exception:
            logging.exception("[MUSIC] Global restore failure")

    # =====================================================
    # READY
    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s (%s)", self.user, self.user.id)

        if not self.dev_guild_id and self.guilds:
            self.dev_guild_id = self.guilds[0].id
            logging.info("[CMD] Auto dev guild set: %s", self.dev_guild_id)

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
    # WAVELINK EVENTS (🔥 CRITICAL FIX FOR UI + SKIP)
    # =====================================================
    async def on_wavelink_track_end(self, payload):
        try:
            await engine._play_next(payload.player)
        except Exception:
            logging.exception("[MUSIC] track_end failed")

    async def on_wavelink_track_exception(self, payload):
        try:
            await engine._play_next(payload.player)
        except Exception:
            logging.exception("[MUSIC] track_exception failed")

    async def on_wavelink_track_stuck(self, payload):
        try:
            await engine._play_next(payload.player)
        except Exception:
            logging.exception("[MUSIC] track_stuck failed")

    # =====================================================
    # LAVALINK READY
    # =====================================================
    async def on_wavelink_node_ready(self, payload):
        logging.info("[LAVALINK] Node ready: %s", payload.node.identifier)

    # =====================================================
    # SHUTDOWN
    # =====================================================
    async def close(self):
        logging.info("[SHUTDOWN] Cleaning up bot...")

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