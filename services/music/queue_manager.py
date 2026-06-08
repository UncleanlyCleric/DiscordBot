from collections import deque
from typing import Optional, List


class QueueManager:

    def __init__(self):
        self.queues = {}  # guild_id -> deque
        self.current = {}  # guild_id -> track

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    def add(self, guild_id: int, tracks: List):
        q = self.get_queue(guild_id)
        for t in tracks:
            q.append(t)

    def next(self, guild_id: int):
        q = self.get_queue(guild_id)
        if not q:
            return None
        return q.popleft()

    def clear(self, guild_id: int):
        self.queues[guild_id] = deque()
        self.current[guild_id] = None

    def set_current(self, guild_id: int, track):
        self.current[guild_id] = track

    def get_current(self, guild_id: int):
        return self.current.get(guild_id)


queue_manager = QueueManager()