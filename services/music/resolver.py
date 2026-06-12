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

        # =====================================================
        # URL DETECTION
        # =====================================================

        is_url = (
            query.startswith("http")
            or re.search(APPLE_MUSIC, query)
            or re.search(SPOTIFY, query)
        )

        try:

            if is_url:

                results = await wavelink.Playable.search(
                    query
                )

            else:

                results = await wavelink.Playable.search(
                    f"ytmsearch:{query}"
                )

                # =================================================
                # SEARCH DEBUG
                # =================================================

                for i, track in enumerate(results[:10], start=1):
                    print(
                        f"[SEARCH] {i}. "
                        f"title={getattr(track, 'title', '')} | "
                        f"author={getattr(track, 'author', '')}"
                    )

        except Exception:
            return []

        if not results:
            return []

        # =====================================================
        # PLAYLISTS
        # =====================================================

        playlist = getattr(
            results,
            "playlist",
            None
        )

        if (
            playlist
            or isinstance(
                results,
                wavelink.Playlist
            )
        ):

            tracks = getattr(
                results,
                "tracks",
                results
            )

            return [
                Track(
                    title=t.title,
                    author=getattr(
                        t,
                        "author",
                        None
                    ),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                    artwork=getattr(
                        t,
                        "artwork",
                        None
                    ),
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
                    author=getattr(
                        t,
                        "author",
                        None
                    ),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                    artwork=getattr(
                        t,
                        "artwork",
                        None
                    ),
                )
                for t in results
            ]

        # =====================================================
        # FILTER BAD RESULTS
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
        # LOCAL RANKING
        # =====================================================

        def score(track):

            title = (
                getattr(track, "title", "") or ""
            ).lower()

            author = (
                getattr(track, "author", "") or ""
            ).lower()

            query_l = query.lower()

            score = 0

            # exact artist
            if author == query_l:
                score += 100

            # artist contains query
            if query_l in author:
                score += 50

            # title contains query
            if query_l in title:
                score += 25

            query_words = set(query_l.split())

            score += len(
                query_words &
                set(author.split())
            ) * 10

            score += len(
                query_words &
                set(title.split())
            ) * 5

            return score

        results = sorted(
            results,
            key=score,
            reverse=True
        )

        # =====================================================
        # SMART PICK
        # =====================================================

        best = pick_best(
            results,
            query
        )

        if not best:
            return []

        print(
            f"[PICKED] "
            f"title={best.title} | "
            f"author={getattr(best, 'author', '')}"
        )

        return [
            Track(
                title=best.title,
                author=getattr(
                    best,
                    "author",
                    None
                ),
                uri=best.uri,
                requester_id=requester_id,
                playable=best,
                artwork=getattr(
                    best,
                    "artwork",
                    None
                ),
            )
        ]


music_resolver = MusicResolver()