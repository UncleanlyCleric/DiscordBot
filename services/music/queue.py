from collections import deque
from typing import List, Optional
import random

from services.music.models import Track


class MusicQueue:
    """
    In-memory queue for active session.
    Persistence handled separately.
    """

    def __init__(self):
        self._queue = deque()

    # =====================================================
    # ADD
    # =====================================================

    def add(self, track: Track):
        self._queue.append(track)

    def add_many(self, tracks: List[Track]):
        self._queue.extend(tracks)

    def add_front(self, track):
        self._queue.appendleft(track)
    

    # =====================================================
    # PLAYBACK
    # =====================================================

    def next(self) -> Optional[Track]:

        if not self._queue:
            return None

        return self._queue.popleft()

    def peek(self) -> Optional[Track]:

        if not self._queue:
            return None

        return self._queue[0]

    # =====================================================
    # MANAGEMENT
    # =====================================================

    def remove(self, index: int) -> Optional[Track]:

        if index < 0 or index >= len(self._queue):
            return None

        temp = list(self._queue)

        removed = temp.pop(index)

        self._queue = deque(temp)

        return removed

    def shuffle(self):

        if len(self._queue) <= 1:
            return

        temp = list(self._queue)

        random.shuffle(temp)

        self._queue = deque(temp)

    def clear(self):
        self._queue.clear()

    # =====================================================
    # VIEW
    # =====================================================

    def all(self) -> List[Track]:
        return list(self._queue)

    def first(self, amount: int = 10) -> List[Track]:
        return list(self._queue)[:amount]

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    # =====================================================
    # MAGIC
    # =====================================================

    def __len__(self):
        return len(self._queue)

    def __bool__(self):
        return bool(self._queue)