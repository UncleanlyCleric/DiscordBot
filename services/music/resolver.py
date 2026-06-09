import re
import wavelink

from services.music.models import Track
from services.music.smart_rank import pick_best

APPLE_MUSIC = r"music.apple.com"
SPOTIFY = r"open.spotify.com"


class MusicResolver:

    async def resolve(self, query: str, requester_id: int):

        query = query.strip()

        if not query:
            return []

        try:
            results = await wavelink.Playable.search(query)

        except Exception as e:
            print(f"[Resolver] search failed: {e}")
            return []

        if not results:
            return []

        # =====================================================
        # FIX 1: REAL PLAYLIST SUPPORT (LavaSrc-safe)
        # =====================================================
        # Some Lavalink setups return playlists via attribute, not type
        playlist = getattr(results, "playlist", None)

        if playlist or isinstance(results, wavelink.Playlist):

            tracks = getattr(results, "tracks", results)

            print(
                f"[Resolver] Playlist detected: "
                f"{getattr(results, 'name', 'unknown')} "
                f"({len(tracks)} tracks)"
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
        # FIX 2: URL HANDLING (Apple Music / Spotify SAFE PATH)
        # =====================================================
        if (
            re.search(APPLE_MUSIC, query)
            or re.search(SPOTIFY, query)
            or query.startswith("http")
        ):

            # Apple Music often returns multiple results even for URLs
            if isinstance(results, list) and len(results) > 1:
                print(f"[Resolver] URL multi-result fallback: {len(results)} tracks")

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

            first = results[0]

            return [
                Track(
                    title=first.title,
                    author=getattr(first, "author", None),
                    uri=first.uri,
                    requester_id=requester_id,
                    playable=first,
                )
            ]

        # =====================================================
        # TEXT SEARCH
        # =====================================================
        best = pick_best(results, query)

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