import time
from music.manager import MusicManager

managers: dict[int, MusicManager] = {}


def get_manager(guild_id: int) -> MusicManager:
    if guild_id not in managers:
        managers[guild_id] = MusicManager(guild_id)
    return managers[guild_id]


def remove_manager(guild_id: int):
    managers.pop(guild_id, None)


def cleanup_managers(timeout: int = 3600):
    now = time.time()
    to_remove = []

    for gid, mgr in managers.items():
        if now - mgr.last_active > timeout:
            to_remove.append(gid)

    for gid in to_remove:
        managers.pop(gid, None)