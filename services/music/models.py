from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Track:
    """
    Internal music track representation.

    IMPORTANT:
    _wavelink_track must store the REAL Playable object
    from wavelink.Playable.search().
    """

    title: str
    author: Optional[str]
    uri: str
    source: Optional[str]

    requester_id: Optional[int] = None

    # 🔥 CRITICAL: this is what actually gets played
    _wavelink_track: Any = None