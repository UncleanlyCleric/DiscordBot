import re
import wavelink
from services.music.models import Track


APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"


class MusicResolver:
    """
    Production-safe resolver.
    Compatible with strict Track schema.
    """

    async def resolve(self, query: str, requester_id: int):

        query = query.strip()

        if not query:
            return []

        # =====================================================
        # URL DETECTION
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
        # PLAYLIST HANDLING
        # =====================================================
        if isinstance(results, wavelink.Playlist):

            for item in results.tracks:
                tracks.append(
                    Track(
                        title=item.title,
                        uri=item.uri,
                        author=getattr(item, "author", None),
                        requester_id=requester_id,
                    )
                )

            return tracks

        # =====================================================
        # SINGLE TRACK ONLY (SPOTIFY MODE)
        # =====================================================
        top = results[0]

        tracks.append(
            Track(
                title=top.title,
                uri=top.uri,
                author=getattr(top, "author", None),
                requester_id=requester_id,
            )
        )

        return tracks

    # =====================================================
    # URL NORMALIZER
    # =====================================================
    async def _convert_url(self, url: str) -> str:

        cleaned = re.sub(r"https?://", "", url)

        cleaned = re.sub(
            r"(music\.apple\.com|open\.spotify\.com)",
            "",
            cleaned
        )

        cleaned = cleaned.replace("/", " ")
        cleaned = cleaned.replace("-", " ")
        cleaned = cleaned.replace("_", " ")

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned


music_resolver = MusicResolver()