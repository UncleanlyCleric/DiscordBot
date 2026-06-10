from dataclasses import dataclass, field
from typing import Any, Optional

from services.music.queue import MusicQueue


@dataclass
class MusicState:
    """
    Per-guild music state container.
    """

    queue: MusicQueue = field(
        default_factory=MusicQueue
    )

    current: Any = None

    # UI tracking
    player_message_id: Optional[int] = None
    player_channel_id: Optional[int] = None

    # timing
    current_started_at: Optional[float] = None
    current_duration: Optional[int] = None


class MusicManager:

    def __init__(self):
        self._states: dict[int, MusicState] = {}

    def get_player(
        self,
        guild_id: int
    ) -> MusicState:

        if guild_id not in self._states:

            self._states[guild_id] = MusicState()

        return self._states[guild_id]

    def get_all(self):

        return self._states.values()


music_manager = MusicManager()