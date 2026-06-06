import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

from utils.logger import setup_logger
from utils.db import init as init_db

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

    async def setup_hook(self):
        self.logger.info("Starting setup_hook...")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # DB INIT
        await init_db()
        self.logger.info("SQLite initialized")

        # LAVALINK (ONLY PLACE IT EXISTS)
        await wavelink.Pool.connect(
            nodes=[
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ],
            client=self
        )

        # LOAD COGS
        extensions = [
            "cogs.music",
            "cogs.quotes",
            "cogs.admin",
            "cogs.dice",
            "cogs.help",
            "cogs.logger"
        ]

        for ext in extensions:
            await self.load_extension(ext)
            self.logger.info(f"Loaded {ext}")

        # SLASH SYNC
        synced = await self.tree.sync()
        self.logger.info(f"Slash sync: {len(synced)} commands")

        self.logger