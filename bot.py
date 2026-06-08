import os
import discord
from discord.ext import commands

from utils.logger import logger
from utils.db import db

TOKEN = (os.getenv("DISCORD_TOKEN") or "").strip()


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.logger = logger
        self.db = db

    async def setup_hook(self):
        self.logger.info("Loading cogs...")

        loaded = 0
        failed = 0

        for file in os.listdir("./cogs"):
            if not file.endswith(".py"):
                continue

            if file.startswith("_"):
                continue

            if file == "config.py":
                continue

            ext = f"cogs.{file[:-3]}"

            try:
                await self.load_extension(ext)

                loaded += 1

                self.logger.info(
                    f"Loaded {ext}"
                )

            except Exception:
                failed += 1

                self.logger.exception(
                    f"Failed to load {ext}"
                )

        self.logger.info(
            f"Cogs loaded. Success={loaded} Failed={failed}"
        )

        self.logger.info(
            "=== COMMAND TREE BEFORE SYNC ==="
        )

        for cmd in self.tree.get_commands():
            self.logger.info(
                f"/{cmd.name}"
            )

        try:
            synced = await self.tree.sync()

            self.logger.info(
                f"Synced {len(synced)} slash commands"
            )

            self.logger.info(
                "=== COMMANDS RETURNED BY DISCORD ==="
            )

            for cmd in synced:
                self.logger.info(
                    f"Registered /{cmd.name}"
                )

        except Exception:
            self.logger.exception(
                "Slash command sync failed"
            )

    async def on_ready(self):
        self.logger.info(
            f"Logged in as {self.user} "
            f"(ID: {self.user.id})"
        )

        self.logger.info(
            f"Application ID: {self.application_id}"
        )

        self.logger.info(
            "Bot is ready."
        )


def main():
    if not TOKEN:
        raise RuntimeError(
            "Missing DISCORD_TOKEN"
        )

    bot = Bot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()