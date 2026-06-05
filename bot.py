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


intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.voice_states = True


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

    # =====================================================
    # MESSAGE ROUTER (IMPORTANT FIX)
    # =====================================================
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild:
            quotes = self.get_cog("Quotes")
            if quotes:
                await quotes.handle_raw_message(message)

        await self.process_commands(message)


if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)