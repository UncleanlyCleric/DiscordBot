import asyncio
import time


class GuildMusic:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.now_playing = None
        self.autoplay = True
        self.last_active = time.time()

    def touch(self):
        """Update last active time when used."""
        self.last_active = time.time()


music_states: dict[int, GuildMusic] = {}


def get_state(gid: int) -> GuildMusic:
    if gid not in music_states:
        music_states[gid] = GuildMusic()

    state = music_states[gid]
    state.touch()
    return state


def clear_state(gid: int):
    music_states.pop(gid, None)


def cleanup_inactive(timeout: int = 3600):
    """
    Remove inactive guild states (default 1 hour).
    Call periodically from bot loop.
    """
    now = time.time()
    to_remove = []

    for gid, state in music_states.items():
        if now - state.last_active > timeout:
            to_remove.append(gid)

    for gid in to_remove:
        music_states.pop(gid, None)