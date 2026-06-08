from typing import List
import wavelink

from services.music.models import Track
from services.music.url_resolver import url_resolver


class MusicResolver:

    async def resolve(self, query: str, requester_id: int) -> List[Track]:

        # 🔥 convert Apple Music URLs → search query
        query = await url_resolver.resolve(query)

        results = await wavelink.Playable.search(query)

        if not results:
            return []

        if isinstance(results, wavelink.Playlist):
            items = results.tracks
        else:
            items = results

        return [
            Track(
                title=t.title,
                author=t.author,
                uri=t.uri,
                requester_id=requester_id,
                playable=t
            )
            for t in items
        ]


music_resolver = MusicResolver()