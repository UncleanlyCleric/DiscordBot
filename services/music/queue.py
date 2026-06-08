from collections import deque
from typing import List, Optional

from services.music.models import Track


class MusicQueue:
    """
    In-memory queue for active session.
    Persistence handled separately.
    """

    def __init__(self):
        self._queue = deque()

    def add(self, track: Track):
        self._queue.append(track)

    def add_many(self, tracks: List[Track]):
        for t in tracks:
            self.add(t)

    def next(self) -> Optional[Track]:
        if not self._queue:
            return None
        return self._queue.popleft()

    def peek(self) -> Optional[Track]:
        return self._queue[0] if self._queue else None

    def remove(self, index: int) -> Optional[Track]:
        if index < 0 or index >= len(self._queue):
            return None

        temp = list(self._queue)
        removed = temp.pop(index)
        self._queue = deque(temp)
        return removed

    def clear(self):
        self._queue.clear()

    def all(self) -> List[Track]:
        return list(self._queue)

    def __len__(self):
        return len(self._queue)