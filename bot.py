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

    # =====================================================
    # STARTUP
    # =====================================================
    async def setup_hook(self):
        self.logger.info("Starting setup_hook...")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        await init_db()

        await wavelink.Pool.connect(
            nodes=[
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ],
            client=self
        )

        extensions = [
            "cogs.quotes",
            "cogs.music",
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
                self.logger.error(f"Failed {ext}: {e}")

        await self.tree.sync()
        self.logger.info("Slash sync complete")

    # =====================================================
    # MESSAGE ROUTER (FIXED — NO COMMAND CONFLICTS)
    # =====================================================
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.strip()

        # -------------------------------------------------
        # 1. ALWAYS RUN QUOTES RAW ROUTER FIRST
        # -------------------------------------------------
        quotes = self.get_cog("Quotes")
        if quotes:
            await quotes.handle_raw_message(message)

        # -------------------------------------------------
        # 2. BLOCK CUSTOM !<category> FROM ENTERING COMMAND SYSTEM
        # -------------------------------------------------
        if content.startswith("!") and len(content) > 1:
            after = content[1:]

            # if it's !<category> (no space), STOP HERE
            # prevents discord.py CommandNotFound spam
            if " " not in after:
                return

        # -------------------------------------------------
        # 3. NORMAL PREFIX COMMANDS ONLY
        # -------------------------------------------------
        await self.process_commands(message)

    # =====================================================
    # SILENTLY IGNORE UNKNOWN COMMANDS
    # =====================================================
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        self.logger.error(f"Command error: {error}")
        raise error


# =====================================================
# RUN BOT
# =====================================================
if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)