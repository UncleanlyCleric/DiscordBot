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
        # QUERY PARSING (kept, but now used for real fix)
        # =====================================================

        def parse_query(q: str):
            q = q.strip()
            parts = q.split()

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

                # =====================================================
                # 🔥 FIX 1: ARTIST-LOCKED SEARCH (PREVENT DRIFT)
                # =====================================================

                artist = parsed["artist"] or query
                track = parsed["track"]

                # Step 1: search ONLY artist (reduces garbage results)
                artist_results = await wavelink.Playable.search(
                    f"ytmsearch:{artist}"
                )

                # Step 2: post-filter by track (if we have one)
                if track and track != artist:
                    filtered_results = [
                        t for t in artist_results
                        if track.lower() in (t.title or "").lower()
                    ]

                    results = filtered_results if filtered_results else artist_results
                else:
                    results = artist_results

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
        # (kept intact, still useful as secondary ranking)
        # =====================================================

        def score(track, query: str):

            q = query.lower()
            title = (getattr(track, "title", "") or "").lower()
            author = (getattr(track, "author", "") or "").lower()

            score = 0

            if q == author:
                score += 200

            if q in author:
                score += 150

            if q in title:
                score += 50

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