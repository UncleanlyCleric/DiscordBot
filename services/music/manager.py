from dataclasses import dataclass, field
from typing import Any, Optional


class Queue:
    def __init__(self):
        self._items = []

    def add(self, item):
        self._items.append(item)

    def next(self):
        if not self._items:
            return None
        return self._items.pop(0)

    def all(self):
        return list(self._items)

    def clear(self):
        self._items.clear()


@dataclass
class MusicState:
    """
    Per-guild music state container.
    """

    queue: Queue = field(default_factory=Queue)

    current: Any = None

    # UI tracking (FIXED)
    player_message_id: Optional[int] = None
    player_channel_id: Optional[int] = None

    # timing
    current_started_at: Optional[float] = None
    current_duration: Optional[int] = None


class MusicManager:
    def __init__(self):
        self._states: dict[int, MusicState] = {}

    def get_player(self, guild_id: int) -> MusicState:
        if guild_id not in self._states:
            self._states[guild_id] = MusicState()
        return self._states[guild_id]

    def get_all(self):
        return self._states.values()


music_manager = MusicManager()