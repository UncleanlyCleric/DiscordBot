import json
import os


class Storage:
    """
    SAFE PERSISTENCE LAYER

    Rules:
    - NO file IO at import time
    - NO global state mutations
    - explicit load/save only
    """

    def __init__(self, base_path="data"):
        self.base_path = base_path
        self.cache = {}

        # ensure folder exists safely
        os.makedirs(self.base_path, exist_ok=True)

    # ---------------------------
    # File Helpers
    # ---------------------------

    def _path(self, filename: str):
        return os.path.join(self.base_path, filename)

    def load_json(self, filename: str):
        """
        Lazy load JSON file.
        Returns empty dict if missing.
        """

        if filename in self.cache:
            return self.cache[filename]

        path = self._path(filename)

        if not os.path.exists(path):
            self.cache[filename] = {}
            return self.cache[filename]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        self.cache[filename] = data
        return data

    def save_json(self, filename: str, data):
        """
        Save JSON safely.
        """

        path = self._path(filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.cache[filename] = data

    # ---------------------------
    # Quotes Example API (your bot likely uses this)
    # ---------------------------

    def add_quote(self, guild_id: str, quote: str):
        data = self.load_json("quotes.json")

        if guild_id not in data:
            data[guild_id] = []

        data[guild_id].append(quote)

        self.save_json("quotes.json", data)

    def get_quotes(self, guild_id: str):
        data = self.load_json("quotes.json")
        return data.get(guild_id, [])


# SAFE SINGLETON (no IO)
storage = Storage()