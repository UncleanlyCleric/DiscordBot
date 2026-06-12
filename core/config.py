import os
import yaml
from pathlib import Path


class Config:
    def __init__(self):
        self.discord_token = os.getenv("DISCORD_TOKEN")

        self.lavalink_uri = os.getenv("LAVALINK_URI", "http://localhost:2333")
        self.lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

        self.dev_guild_id = int(os.getenv("DEV_GUILD_ID", "0"))

        # 🔥 LOAD YAML CONFIG PROPERLY
        config_path = Path("config.yml")  # adjust if needed

        if config_path.exists():
            with open(config_path, "r") as f:
                self.yaml = yaml.safe_load(f)
        else:
            self.yaml = {}

        self.db_path = self.yaml.get("database", {}).get(
            "path",
            "bot.db"
        )

    def get(self, section: str, key: str):
        return self.yaml.get(section, {}).get(key)
    
config = Config()