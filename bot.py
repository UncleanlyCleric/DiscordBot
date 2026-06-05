import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import wavelink

from music.registry import cleanup_managers, remove_manager

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
            command_prefix="!",
            intents=intents
        )

    # ---------------- STARTUP ----------------
    async def setup_hook(self):
        print("Starting setup_hook...")

        # ---- validation ----
        if not TOKEN:
            raise RuntimeError("Missing DISCORD_TOKEN")

        if not LAVALINK_URI or not LAVALINK_PASSWORD:
            raise RuntimeError("Missing Lavalink config")

        # ---- Lavalink ----
        print("Connecting to Lavalink...")

        try:
            nodes = [
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ]

            await wavelink.Pool.connect(
                nodes=nodes,
                client=self
            )

            print("Lavalink connected")

        except Exception as e:
            print(f"Lavalink connection failed: {e}")
            raise

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

        # ---- background tasks ----
        self.cleanup_task.start()

        print("setup_hook complete")

    # ---------------- CLEANUP LOOP ----------------
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        try:
            cleanup_managers(timeout=3600)
        except Exception as e:
            print(f"Cleanup error: {e}")

    # ---------------- EVENTS ----------------
async def on_ready(self):
    try:
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    print(f"\nLogged in as {self.user} (ID: {self.user.id})")

    print("\n========== PREFIX COMMANDS ==========")
    if self.commands:
        for cmd in sorted(self.commands, key=lambda c: c.name):
            print(f" - {cmd.name}")
    else:
        print("No prefix commands loaded.")

    print("\n========== SLASH COMMANDS ==========")
    slash_commands = self.tree.get_commands()

    if slash_commands:
        for cmd in sorted(slash_commands, key=lambda c: c.name):
            print(f" - /{cmd.name}")
    else:
        print("No slash commands loaded.")

    print("\n========== COGS ==========")
    if self.cogs:
        for cog in sorted(self.cogs):
            print(f" - {cog}")
    else:
        print("No cogs loaded.")

    print("\nBot ready.\n")

# ---------------- RUN ----------------
if __name__ == "__main__":
    bot = Bot()
    bot.run(TOKEN)
