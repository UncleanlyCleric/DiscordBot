import re
import wavelink

from services.music.models import Track
from services.music.smart_rank import pick_best

APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"

BAD_RESULTS = [
    "karaoke",
    "instrumental",
    "nightcore",
    "8d audio",
    "bass boosted",
    "sped up",
    "slowed",
    "reverb",
    "cover",
    "tribute",
    "reaction",
    "lyrics",
]


class MusicResolver:

    async def resolve(
        self,
        query: str,
        requester_id: int
    ):

        query = query.strip()

        if not query:
            return []

        is_url = (
            query.startswith("http")
            or re.search(APPLE_MUSIC, query)
            or re.search(SPOTIFY, query)
        )

        try:

            # URLs should be resolved normally
            if is_url:
                results = await wavelink.Playable.search(query)

            # Text searches should favor YouTube Music
            else:
                results = await wavelink.Playable.search(
                    f"ytsearch:{query}"
                )

        except Exception:
            return []

        if not results:
            return []

        # =====================================================
        # PLAYLISTS
        # =====================================================

        playlist = getattr(results, "playlist", None)

        if (
            playlist
            or isinstance(results, wavelink.Playlist)
        ):

            tracks = getattr(
                results,
                "tracks",
                results
            )

            return [
                Track(
                    title=t.title,
                    author=getattr(t, "author", None),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                )
                for t in tracks
            ]

        # =====================================================
        # URLS
        # =====================================================

        if is_url:

            return [
                Track(
                    title=t.title,
                    author=getattr(t, "author", None),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                )
                for t in results
            ]

        # =====================================================
        # FILTER GARBAGE RESULTS
        # =====================================================

        filtered = []

        for track in results:

            title = getattr(
                track,
                "title",
                ""
            ).lower()

            if any(
                bad in title
                for bad in BAD_RESULTS
            ):
                continue

            filtered.append(track)

        if filtered:
            results = filtered

        # =====================================================
        # SMART PICK
        # =====================================================

        best = pick_best(
            results,
            query
        )

        if not best:
            return []

        return [
            Track(
                title=best.title,
                author=getattr(best, "author", None),
                uri=best.uri,
                requester_id=requester_id,
                playable=best,
            )
        ]


music_resolver = MusicResolver()