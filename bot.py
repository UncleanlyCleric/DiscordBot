import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink
import traceback

from utils.logger import setup_logger
from utils.db import init as init_db

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URI = os.getenv("LAVALINK_URI")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")


# =====================================================
# INTENTS (CRITICAL)
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
    # SETUP HOOK (FULL DEBUG)
    # =====================================================
    async def setup_hook(self):
        print("\n[BOOT] setup_hook started")

        # ---------------- TOKEN CHECK ----------------
        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # ---------------- DB ----------------
        print("[BOOT] init db...")
        await init_db()

        # ---------------- LAVALINK ----------------
        print("[BOOT] connecting wavelink...")

        try:
            await wavelink.Pool.connect(
                nodes=[
                    wavelink.Node(
                        uri=LAVALINK_URI,
                        password=LAVALINK_PASSWORD
                    )
                ],
                client=self
            )
            print("[BOOT] wavelink connected")
        except Exception as e:
            print("[BOOT] WAVELINK FAILED:", e)
            traceback.print_exc()

        # ---------------- COGS ----------------
        extensions = [
            "cogs.quotes",
            "cogs.music",
            "cogs.admin",
            "cogs.dice",
            "cogs.help",
            "cogs.logger"
        ]

        print("[BOOT] loading cogs...")

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"[BOOT] LOADED: {ext}")
            except Exception as e:
                print(f"[BOOT] FAILED COG: {ext}")
                traceback.print_exc()

        # ---------------- SLASH SYNC ----------------
        print("[BOOT] syncing slash commands...")

        try:
            synced = await self.tree.sync()
            print(f"[BOOT] SLASH SYNC COMPLETE: {len(synced)} commands")
        except Exception as e:
            print("[BOOT] SLASH SYNC FAILED:", e)
            traceback.print_exc()

        print("[BOOT] setup_hook finished\n")

    # =====================================================
    # MESSAGE DEBUG PIPELINE
    # =====================================================
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        print(f"[MESSAGE] {message.author}: {message.content}")

        # IMPORTANT: do not block commands
        try:
            await self.process_commands(message)
        except Exception as e:
            print("[COMMAND ERROR]", e)
            traceback.print_exc()

        # optional raw system debug
        try:
            quotes = self.get_cog("Quotes")
            if quotes:
                await quotes.handle_raw_message(message)
        except Exception as e:
            print("[QUOTES ERROR]", e)
            traceback.print_exc()

    # =====================================================
    # COMMAND DEBUG
    # =====================================================
    async def on_command(self, ctx):
        print(f"[COMMAND] {ctx.command} by {ctx.author}")

    async def on_command_error(self, ctx, error):
        print(f"[COMMAND ERROR] {error}")
        traceback.print_exception(type(error), error, error.__traceback__)

        if isinstance(error, commands.CommandNotFound):
            return

        raise error


# =====================================================
# RUN BOT
# =====================================================
if __name__ == "__main__":
    print("[BOOT] starting bot...")

    bot = Bot()
    bot.run(TOKEN)