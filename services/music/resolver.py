import re
import wavelink


APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"


class MusicResolver:

    async def resolve(self, query: str, requester_id: int):

        query = query.strip()

        # --------------------------
        # Apple Music / Spotify URL
        # --------------------------
        if re.search(APPLE_MUSIC, query) or re.search(SPOTIFY, query):
            query = await self._convert_url(query)

        results = await wavelink.Playable.search(query)

        if not results:
            return []

        items = results.tracks if isinstance(results, wavelink.Playlist) else results

        return [
            type("Track", (), {
                "title": t.title,
                "uri": t.uri,
                "playable": t,
                "requester_id": requester_id
            })()
            for t in items
        ]

    async def _convert_url(self, url: str) -> str:
        """
        Spotify/Apple Music → search query fallback.
        Production systems use official APIs here.
        """

        # simple fallback extraction
        cleaned = re.sub(r"https?://", "", url)
        cleaned = cleaned.replace("/", " ")
        cleaned = cleaned.replace("-", " ")

        return cleaned


music_resolver = MusicResolver()