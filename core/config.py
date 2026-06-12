import os


class Config:
    """
    Single-source configuration system (ENV ONLY).
    No YAML ambiguity. No silent fallbacks.
    """

    def __init__(self):
        # Core
        self.discord_token = os.getenv("DISCORD_TOKEN")

        # Lavalink
        self.lavalink_uri = os.getenv(
            "LAVALINK_URI",
            "http://lavalink:2333"
        )

        self.lavalink_password = os.getenv(
            "LAVALINK_PASSWORD",
            "youshallnotpass"
        )

        # DATABASE (IMPORTANT FIX)
        self.db_path = os.getenv(
            "DATABASE_PATH",
            "storage/db/bot.db"
        )

        # Dev guild
        self.dev_guild_id = int(
            os.getenv("DEV_GUILD_ID", "0")
        )

    def get(self, key: str, default=None):
        """
        Simple ENV accessor only (no YAML).
        """
        return os.getenv(key.upper(), default)


config = Config()