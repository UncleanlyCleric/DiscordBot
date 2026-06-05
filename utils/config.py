import json
import os

CONFIG_PATH = "data/guild_config.json"


def _load():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


config_cache = _load()


def get(guild_id: int):
    return config_cache.get(str(guild_id), {
        "dj_role_id": None,
        "markov_channel_id": None,
        "markov_training": True
    })


def set_value(guild_id: int, key: str, value):
    gid = str(guild_id)

    if gid not in config_cache:
        config_cache[gid] = get(guild_id)

    config_cache[gid][key] = value
    _save(config_cache)