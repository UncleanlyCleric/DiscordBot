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

        # =====================================================
        # 🎯 NEW: QUERY PARSING (MAJOR FIX)
        # =====================================================

        def parse_query(q: str):
            q = q.strip()
            parts = q.split()

            # heuristic: "artist + track"
            if len(parts) >= 2:
                return {
                    "artist": " ".join(parts[:-1]),
                    "track": parts[-1],
                    "raw": q
                }

            return {
                "artist": None,
                "track": q,
                "raw": q
            }

        parsed = parse_query(query)

        try:

            if is_url:

                results = await wavelink.Playable.search(
                    query
                )

            else:

                # =================================================
                # 🔥 FIX: SMART QUERY REWRITE
                # =================================================

                if parsed["artist"] and parsed["track"]:
                    search_query = f'{parsed["artist"]} - {parsed["track"]}'
                else:
                    search_query = query

                results = await wavelink.Playable.search(
                    f"ytmsearch:{search_query}"
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
        # FILTER BAD RESULTS (SAFE VERSION)
        # =====================================================

        query_lower = query.lower()
        artist_intent = len(query_lower.split()) <= 4

        filtered = []

        for track in results:

            title = getattr(
                track,
                "title",
                ""
            ).lower()

            # only filter aggressively when NOT artist intent
            if any(
                bad in title
                for bad in BAD_RESULTS
            ):
                if not artist_intent:
                    continue

            filtered.append(track)

        if filtered:
            results = filtered

        # =====================================================
        # ARTIST-AWARE RANKING BOOST
        # =====================================================

        def score(track, query: str):

            q = query.lower()
            title = (getattr(track, "title", "") or "").lower()
            author = (getattr(track, "author", "") or "").lower()

            score = 0

            # 🎯 exact artist match
            if q == author:
                score += 200

            # 🎯 artist contains query
            if q in author:
                score += 150

            # 🎧 title match
            if q in title:
                score += 50

            # 🔎 word overlap
            if any(word in author for word in q.split()):
                score += 30

            return score

        results = sorted(
            results,
            key=lambda t: score(t, query),
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