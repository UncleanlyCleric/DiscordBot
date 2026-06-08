from dataclasses import dataclass
from typing import Optional
import wavelink


@dataclass
class Track:
    title: str
    author: Optional[str]
    uri: str
    requester_id: int

    # 🔥 REAL PLAYABLE (MANDATORY)
    playable: wavelink.Playable = None