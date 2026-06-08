import random

from services.music.models import Track


class AutoplayEngine:
    """
    Generates fallback tracks when queue is empty.

    Later upgrade:
    - YouTube related videos
    - Spotify radio mapping
    """

    def generate(self, last_track: Track | None) -> Track | None:
        if not last_track:
            return None

        # simple deterministic fallback for now
        return Track(
            title=f"Autoplay mix based on {last_track.title}",
            author=last_track.author,
            uri=f"ytsearch:{last_track.title} mix",
            source="autoplay",
            requester_id=None
        )


autoplay_engine = AutoplayEngine()