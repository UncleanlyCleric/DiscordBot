from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    title: str
    author: Optional[str]
    uri: str
    source: Optional[str]
    requester_id: Optional[int] = None


@dataclass
class PlayerState:
    guild_id: int
    is_playing: bool = False
    volume: int = 75
    repeat_mode: str = "off"  # off | track | queue
    shuffle: bool = False