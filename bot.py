import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import wavelink

from music.registry import cleanup_managers
from utils.logger import setup_logger
from utils.db import init as init_db

print("START DIR:", os.getcwd())
print("WRITE TEST:", os.access(".", os.W_OK))

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URI = os.getenv("LAVALINK_URI")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")


# =====================================================
# INTENTS
# =====================================================
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.voice_states = True


# =====================================================
# BOT CLASS
# =====================================================
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        self.logger = setup_logger()

    # =====================================================
    # STARTUP HOOK
    # =====================================================
    async def setup_hook(self):
        self.logger.info("Starting setup_hook...")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # =====================================================
        # DB INIT
        # =====================================================
        try:
            await init_db()
            self.logger.info("SQLite initialized")
        except Exception as e:
            self.logger.error(f"DB init failed: {e}")
            raise

        # =====================================================
        # LAVALINK CONNECT
        # =====================================================
        try:
            self.logger.info("Connecting to Lavalink...")

            await wavelink.Pool.connect(
                nodes=[
                    wavelink.Node(
                        uri=LAVALINK_URI,
                        password=LAVALINK_PASSWORD
                    )
                ],
                client=self
            )

            self.logger.info("Lavalink connected")

        except Exception as e:
            self.logger.error(f"Lavalink connection failed: {e}")
            raise

        # =====================================================
        # LOAD COGS
        # =====================================================
        extensions = [
            "cogs.music",
            "cogs.quotes",
            "cogs.admin",
            "cogs.dice",
            "cogs.help",
            "cogs.logger"
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                self.logger.info(f"Loaded {ext}")
            except Exception as e:
                self.logger.error(f"Failed to load {ext}: {e}")

        # =====================================================
        # IMPORTANT: SINGLE SLASH SYNC ONLY
        # =====================================================
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Global slash sync: {len(synced)} commands")
        except Exception as e:
            self.logger.error(f"Slash sync failed: {e}")

        # =====================================================
        # TASKS
        # =====================================================
        self.cleanup_task.start()
        self.logger.info("setup_hook complete")

    # =====================================================
    # CLEANUP LOOP
    # =====================================================
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        try:
            cleanup_managers(timeout=3600)
            self.logger.info("Cleanup task executed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    # =====================================================
    # MESSAGE HANDLER (PREFIX COMMANDS)
    # =====================================================
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)


# =====================================================
# RUN BOT
# =====================================================
if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)