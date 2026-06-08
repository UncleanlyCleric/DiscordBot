from collections import defaultdict
import logging

log = logging.getLogger(__name__)


class MusicManager:
    """
    SAFE MUSIC CORE SERVICE

    Rules:
    - NO discord imports
    - NO UI imports
    - NO DB imports
    - NO initialization at import time
    """

    def __init__(self):
        # guild_id -> queue list
        self.queues = defaultdict(list)

        # guild_id -> current track state
        self.current = {}

        # guild_id -> voice state (injected later)
        self.voice_clients = {}

    # ---------------------------
    # Queue Management
    # ---------------------------

    def add_to_queue(self, guild_id: int, track: dict):
        self.queues[guild_id].append(track)

        log.debug(
            "Track queued (guild=%s, size=%s)",
            guild_id,
            len(self.queues[guild_id])
        )

    def get_queue(self, guild_id: int):
        return self.queues[guild_id]

    def clear_queue(self, guild_id: int):
        self.queues[guild_id].clear()

        log.debug(
            "Queue cleared (guild=%s)",
            guild_id
        )

    def queue_size(self, guild_id: int) -> int:
        return len(self.queues[guild_id])

    def has_queue(self, guild_id: int) -> bool:
        return bool(self.queues[guild_id])

    def peek_next(self, guild_id: int):
        queue = self.queues[guild_id]

        if not queue:
            return None

        return queue[0]

    # ---------------------------
    # Playback State
    # ---------------------------

    def set_current(self, guild_id: int, track: dict):
        self.current[guild_id] = track

    def get_current(self, guild_id: int):
        return self.current.get(guild_id)

    def clear_current(self, guild_id: int):
        self.current.pop(guild_id, None)

    # ---------------------------
    # Voice Layer (injected)
    # ---------------------------

    def set_voice(self, guild_id: int, voice_client):
        self.voice_clients[guild_id] = voice_client

    def get_voice(self, guild_id: int):
        return self.voice_clients.get(guild_id)

    def remove_voice(self, guild_id: int):
        self.voice_clients.pop(guild_id, None)

    # ---------------------------
    # Playback Logic Hooks
    # ---------------------------

    def next_track(self, guild_id: int):
        queue = self.queues[guild_id]

        if not queue:
            self.clear_current(guild_id)
            return None

        track = queue.pop(0)
        self.set_current(guild_id, track)

        log.debug(
            "Dequeued track (guild=%s, remaining=%s)",
            guild_id,
            len(queue)
        )

        return track

    # ---------------------------
    # Cleanup
    # ---------------------------

    def cleanup_guild(self, guild_id: int):
        """
        Completely remove guild state.

        Call when:
        - bot disconnects
        - queue finishes
        - guild removed
        """

        self.queues.pop(guild_id, None)
        self.current.pop(guild_id, None)
        self.voice_clients.pop(guild_id, None)

        log.info(
            "Guild music state cleaned up (guild=%s)",
            guild_id
        )


# Singleton instance (safe, no side effects)
music_manager = MusicManager()