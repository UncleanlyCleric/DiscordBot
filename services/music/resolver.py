import re
import wavelink

from services.music.models import Track
from services.music.smart_rank import pick_best


APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"


class MusicResolver:

    async def resolve(self, query: str, requester_id: int):

        query = query.strip()

        if not query:
            return []

        # URL normalization
        if re.search(APPLE_MUSIC, query) or re.search(SPOTIFY, query):
            query = await self._convert_url(query)

        try:
            results = await wavelink.Playable.search(query)
        except Exception as e:
            print(f"[Resolver] search failed: {e}")
            return []

        if not results:
            return []

        # playlist support unchanged
        if isinstance(results, wavelink.Playlist):

            return [
                Track(
                    title=t.title,
                    uri=t.uri,
                    author=getattr(t, "author", None),
                    requester_id=requester_id,
                )
                for t in results.tracks
            ]

        # 🔥 SMART PICK instead of results[0]
        best = pick_best(results, query)

        if not best:
            return []

        return [
            Track(
                title=best.title,
                uri=best.uri,
                author=getattr(best, "author", None),
                requester_id=requester_id,
            )
        ]

    async def _convert_url(self, url: str) -> str:
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"(music\.apple\.com|open\.spotify\.com)", "", cleaned)
        cleaned = cleaned.replace("/", " ").replace("-", " ").replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned


music_resolver = MusicResolver()