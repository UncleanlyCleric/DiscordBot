from pathlib import Path
import os

import yaml
from dotenv import load_dotenv


load_dotenv()


class Config:
    def __init__(self, config_path: str = "application.yml"):
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(path, "r", encoding="utf-8") as fp:
            self.data = yaml.safe_load(fp)

    def get(self, *keys, default=None):
        value = self.data

        for key in keys:
            if not isinstance(value, dict):
                return default

            value = value.get(key)

            if value is None:
                return default

        return value

    @property
    def discord_token(self) -> str:
        return os.getenv("DISCORD_TOKEN", "")

    @property
    def lavalink_host(self) -> str:
        return os.getenv("LAVALINK_HOST", "localhost")

    @property
    def lavalink_port(self) -> int:
        return int(os.getenv("LAVALINK_PORT", "2333"))

    @property
    def lavalink_password(self) -> str:
        return os.getenv("LAVALINK_PASSWORD", "youshallnotpass")


config = Config()