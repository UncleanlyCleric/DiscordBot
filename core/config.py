import os


class Config:
    def __init__(self):
        self.discord_token = os.getenv("DISCORD_TOKEN")

        self.lavalink_uri = os.getenv("LAVALINK_URI", "http://localhost:2333")
        self.lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

        self.db_path = os.getenv("DATABASE_PATH", "bot.db")

    def get(self, section: str, key: str):
        # backwards compatibility (optional legacy support)
        return os.getenv(f"{section.upper()}_{key.upper()}")


config = Config()