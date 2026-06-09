import re
import wavelink
from services.music.models import Track


APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"


class MusicResolver:
    """
    Production-safe resolver:
    - supports search queries
    - supports Apple Music URLs (fallback)
    - supports Spotify URLs (fallback)
    - returns SINGLE track unless playlist
    """

    async def resolve(self, query: str, requester_id: int):

        query = query.strip()

        if not query:
            return []

        # =====================================================
        # URL DETECTION (Apple / Spotify)
        # =====================================================
        if re.search(APPLE_MUSIC, query) or re.search(SPOTIFY, query):
            query = await self._convert_url(query)

        try:
            results = await wavelink.Playable.search(query)
        except Exception as e:
            print(f"[Resolver] search failed: {e}")
            return []

        if not results:
            return []

        tracks = []

        # =====================================================
        # PLAYLIST SUPPORT (ONLY CASE MULTI IS ALLOWED)
        # =====================================================
        if isinstance(results, wavelink.Playlist):

            for item in results.tracks:
                tracks.append(
                    Track(
                        title=item.title,
                        uri=item.uri,
                        author=getattr(item, "author", None),
                        source=str(getattr(item, "source", None)),
                        requester_id=requester_id,
                    )
                )

            return tracks

        # =====================================================
        # SINGLE TRACK MODE (SPOTIFY BEHAVIOR)
        # =====================================================

        top = results[0]  # ALWAYS ONLY FIRST RESULT

        tracks.append(
            Track(
                title=top.title,
                uri=top.uri,
                author=getattr(top, "author", None),
                source=str(getattr(top, "source", None)),
                requester_id=requester_id,
            )
        )

        return tracks

    # =====================================================
    # URL NORMALIZER (SAFE FALLBACK)
    # =====================================================
    async def _convert_url(self, url: str) -> str:
        """
        Convert Spotify/Apple Music URLs into search queries.

        NOTE:
        Real production systems use Spotify/Apple APIs.
        This is a fallback heuristic.
        """

        # strip protocol
        cleaned = re.sub(r"https?://", "", url)

        # remove domain noise
        cleaned = re.sub(r"(music\.apple\.com|open\.spotify\.com)", "", cleaned)

        # convert separators into search terms
        cleaned = cleaned.replace("/", " ")
        cleaned = cleaned.replace("-", " ")
        cleaned = cleaned.replace("_", " ")

        # collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned


music_resolver = MusicResolver()