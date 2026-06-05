import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import wavelink

from music.registry import cleanup_managers

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URI = os.getenv("LAVALINK_URI")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")


# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.voice_states = True


# ---------------- BOT ----------------
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # only used for quotes
            intents=intents,
            help_command=None
        )

    # ---------------- STARTUP ----------------
    async def setup_hook(self):
        print("Starting setup_hook...")

        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # ---- Lavalink ----
        print("Connecting to Lavalink...")

        nodes = [
            wavelink.Node(
                uri=LAVALINK_URI,
                password=LAVALINK_PASSWORD
            )
        ]

        await wavelink.Pool.connect(nodes=nodes, client=self)

        print("Lavalink connected")

        # ---- cogs ----
        extensions = [
            "cogs.music",
            "cogs.quotes",
            "cogs.admin",
            "cogs.dice"
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"Loaded {ext}")
            except Exception as e:
                print(f"Failed {ext}: {e}")

        # ---- cleanup task ----
        self.cleanup_task.start()

        print("setup_hook complete")

    # ---------------- CLEANUP LOOP ----------------
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        try:
            cleanup_managers(timeout=3600)
        except Exception as e:
            print(f"Cleanup error: {e}")

    # ---------------- PREFIX RESTRICTION ----------------
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # ONLY allow !quote commands
        if message.content.startswith("!"):
            cmd = message.content.split(" ")[0][1:]

            if not cmd.startswith("quote"):
                return  # block everything else

        await self.process_commands(message)

    # ---------------- READY ----------------
    async def on_ready(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"Slash sync failed: {e}")

        print(f"\nLogged in as {self.user} (ID: {self.user.id})")
        print("Bot ready.\n")


# ---------------- RUN ----------------
if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)