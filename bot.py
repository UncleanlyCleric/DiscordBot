import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import wavelink
import logging

from music.registry import cleanup_managers
from utils.logger import setup_logger


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URI = os.getenv("LAVALINK_URI")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")


# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.voice_states = True


# =====================================================
# BOT
# =====================================================
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # 🔥 LOGGER ATTACHED HERE
        self.logger = setup_logger()

    # ---------------- STARTUP ----------------
    async def setup_hook(self):
        self.logger.info("Starting setup_hook...")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # ---- Lavalink ----
        self.logger.info("Connecting to Lavalink...")

        nodes = [
            wavelink.Node(
                uri=LAVALINK_URI,
                password=LAVALINK_PASSWORD
            )
        ]

        await wavelink.Pool.connect(nodes=nodes, client=self)

        self.logger.info("Lavalink connected")

        # ---- cogs ----
        extensions = [
            "cogs.music",
            "cogs.quotes",
            "cogs.admin",
            "cogs.dice",
            "cogs.help",
            "cogs.core_logging"
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                self.logger.info(f"Loaded {ext}")
            except Exception as e:
                self.logger.error(f"Failed to load {ext}: {e}")

        # ---- cleanup task ----
        self.cleanup_task.start()

        self.logger.info("setup_hook complete")

    # ---------------- CLEANUP LOOP ----------------
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        try:
            cleanup_managers(timeout=3600)
            self.logger.info("Cleanup task executed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    # ---------------- PREFIX RESTRICTION ----------------
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.content.startswith("!"):
            cmd = message.content.split(" ")[0][1:]

            if not cmd.startswith("quote"):
                return

        await self.process_commands(message)

    # ---------------- READY ----------------
    async def on_ready(self):
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Slash sync failed: {e}")

        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info("Bot ready.")


# ---------------- RUN ----------------
if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)