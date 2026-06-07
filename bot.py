import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink
import traceback
from discord import app_commands

from utils.logger import setup_logger
from utils.db import init as init_db

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URI = os.getenv("LAVALINK_URI")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

# OPTIONAL (use for fast slash testing)
# GUILD_ID = 1234567890


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
    # SETUP HOOK
    # =====================================================
    async def setup_hook(self):
        print("\n[BOOT] setup_hook started")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        print("[BOOT] init db...")
        await init_db()

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

        # =================================================
        # LOAD COGS
        # =================================================
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
                print(f"[BOOT] loading {ext}...")
                await self.load_extension(ext)
                print(f"[BOOT] LOADED: {ext}")

            except Exception as e:
                print(f"[BOOT] FAILED COG: {ext}")
                traceback.print_exc()

        # =================================================
        # DEBUG COMMAND TREE BEFORE SYNC
        # =================================================
        print("\n[BOOT] COMMAND TREE BEFORE SYNC:")
        for cmd in self.tree.walk_commands():
            print(f" - /{cmd.name}")

        help_cmd = self.get_command("help")
        print("[BOOT] PREFIX HELP COMMAND:", help_cmd)

        # =================================================
        # SLASH SYNC
        # =================================================
        print("\n[BOOT] syncing slash commands...")

        try:
            # OPTIONAL FAST TEST (uncomment if needed)
            # guild = discord.Object(id=GUILD_ID)
            # synced = await self.tree.sync(guild=guild)

            synced = await self.tree.sync()

            print(f"[BOOT] SLASH SYNC COMPLETE: {len(synced)} commands")

            for c in synced:
                print(f"   ↳ /{c.name}")

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

        try:
            await self.process_commands(message)

        except commands.CommandNotFound:
            pass

        except Exception as e:
            print("[COMMAND ERROR]", e)
            traceback.print_exc()

        try:
            quotes = self.get_cog("Quotes")
            if quotes:
                await quotes.handle_raw_message(message)

        except Exception as e:
            print("[QUOTES ERROR]", e)
            traceback.print_exc()

    # =====================================================
    # PREFIX COMMAND DEBUG
    # =====================================================
    async def on_command(self, ctx):
        print(f"[COMMAND] {ctx.command} by {ctx.author}")

    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.HybridCommandError):
            return

        if "CommandNotFound" in str(error):
            return

        command_name = getattr(ctx.command, "name", None) or "unknown"

        self.logger.error(f"ERROR in {command_name}: {error}")

    # =====================================================
    # SLASH / APP COMMAND ERROR HANDLER
    # =====================================================
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if "CommandNotFound" in str(error):
            return

        self.logger.error(f"APP ERROR: {error}")


# =====================================================
# RUN BOT
# =====================================================
if __name__ == "__main__":
    print("[BOOT] starting bot...")

    bot = Bot()
    bot.run(TOKEN)