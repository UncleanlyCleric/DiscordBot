import os


class Config:
    def __init__(self):
        self.discord_token = os.getenv("DISCORD_TOKEN")

        self.lavalink_uri = os.getenv(
            "LAVALINK_URI",
            "http://localhost:2333"
        )

        self.lavalink_password = os.getenv(
            "LAVALINK_PASSWORD",
            "youshallnotpass"
        )

        self.db_path = os.getenv(
            "DATABASE_PATH",
            "bot.db"
        )

        # Development guild for instant slash-command sync
        self.dev_guild_id = int(
            os.getenv("DEV_GUILD_ID", "1512944166382993488")
        )

    def get(self, section: str, key: str):
        return os.getenv(
            f"{section.upper()}_{key.upper()}"
        )


config = Config()