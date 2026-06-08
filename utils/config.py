import os


class Config:
    """
    Centralized config loader.
    SAFE: no IO, no DB, no external calls on import.
    """

    def __init__(self):
        self._loaded = False
        self._cache = {}

    def load(self):
        """
        Loads environment-based config lazily.
        """
        if self._loaded:
            return self._cache

        self._cache = {
            "token": os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN"),
            "db_url": os.getenv("DB_URL"),
            "prefix": os.getenv("PREFIX", "!"),
            "music_enabled": os.getenv("MUSIC_ENABLED", "true").lower() == "true",

            # Markov defaults
            "markov_training": True,
            "markov_channel_id": None,
        }

        self._loaded = True
        return self._cache

    def get(self, key: str, default=None):
        cfg = self.load()
        return cfg.get(key, default)


# ---------------------------
# Singleton
# ---------------------------

config = Config()


# ---------------------------
# Backward Compatibility
# ---------------------------

def get(guild_id=None):
    """
    Legacy API expected by older cogs.

    Old code:
        from utils.config import get as get_cfg
        cfg = get_cfg(guild_id)

    Returns a dict-like config object.
    """

    return config.load()