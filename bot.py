import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

from services.music.ui.music_player_view import MusicPlayerView
import wavelink

from core.logger import setup_logging
from core.config import config
from core.database import db
from core.audit_logger import audit

from database.migrations import migration_runner

from services.music.manager import music_manager
from services.music.player_engine import engine
from services.music.player_message_manager import (
    player_message_manager
)

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
        # DEV GUILD (optional override)
        # =====================================================
        self.dev_guild_id = getattr(config, "dev_guild_id", None)

    # =====================================================
    # BOOT
    # =====================================================
    async def setup_hook(self):
        logging.info("[BOOT] Running migrations...")
        await migration_runner.run()

        logging.info("[BOOT] Connecting DB...")
        await db.connect()

        # =====================================================
        # LAVALINK NODE (Wavelink 4 SAFE CONNECT)
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

        #from services.music.ui.music_player_view import MusicPlayerView

        self.add_view(MusicPlayerView())

        # =====================================================
        # SYNC COMMANDS (PRODUCTION + DEV GUILD MODE)
        # =====================================================
        try:
            # Global sync (slow but required for production rollout)
            global_synced = await self.tree.sync()
            logging.info("[CMD] Global synced %s commands", len(global_synced))

            # Dev guild sync (instant updates)
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
                logging.warning("[CMD] No dev guild available for fast sync")

        except Exception:
            logging.exception("[CMD] Sync failed")

        # =====================================================
        # MUSIC RESTORE (STATE ONLY)
        # =====================================================
        logging.info("[MUSIC] Restoring state...")

        await asyncio.sleep(1)

        for player in music_manager.get_all():
            try:
                tracks = player.queue.all()
                player.queue.clear()
                for t in tracks:
                    player.queue.add(t)
            except Exception:
                logging.exception("[MUSIC] Restore failed %s", player.guild_id)

    # =====================================================
    # READY
    # =====================================================
    async def on_ready(self):
        logging.info("[READY] Logged in as %s (%s)", self.user, self.user.id)

        # fallback dev guild detection
        if not self.dev_guild_id and self.guilds:
            self.dev_guild_id = self.guilds[0].id
            logging.info("[CMD] Auto dev guild set: %s", self.dev_guild_id)

    # =====================================================
    # AUDIT
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
    # LAVALINK READY EVENT
    # =====================================================
    async def on_wavelink_node_ready(self, payload):
        logging.info("[LAVALINK] Node fully ready: %s", payload.node.identifier)

 
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
    setup_logging()

    bot = DiscordBot()

    token = config.discord_token
    if not token:
        raise RuntimeError("DISCORD_TOKEN missing")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())