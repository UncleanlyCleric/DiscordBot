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
            # IMPORTANT:
            # Pass Spotify / Apple Music URLs directly to Lavalink.
            # LavaSrc handles them.
            results = await wavelink.Playable.search(query)

        except Exception as e:
            print(f"[Resolver] search failed: {e}")
            return []

        if not results:
            return []

        # =====================================================
        # PLAYLIST
        # =====================================================
        if isinstance(results, wavelink.Playlist):

            print(
                f"[Resolver] Playlist detected: "
                f"{results.name} ({len(results.tracks)} tracks)"
            )

            return [
                Track(
                    title=t.title,
                    author=getattr(t, "author", None),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                )
                for t in results.tracks
            ]

        # =====================================================
        # DIRECT URL RESULT
        # =====================================================
        if (
            re.search(APPLE_MUSIC, query)
            or re.search(SPOTIFY, query)
            or query.startswith("http")
        ):

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