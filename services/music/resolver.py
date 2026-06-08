from typing import List
import wavelink
from services.music.models import Track


class MusicResolver:

    async def resolve(self, query: str, requester_id: int) -> List[Track]:

        results = await wavelink.Playable.search(query)

        if not results:
            return []

        # Playlist support
        if isinstance(results, wavelink.Playlist):
            items = results.tracks
        else:
            items = results

        tracks: List[Track] = []

        for item in items:
            tracks.append(
                Track(
                    title=item.title,
                    author=item.author,
                    uri=item.uri,
                    requester_id=requester_id,
                    playable=item
                )
            )

        return tracks


music_resolver = MusicResolver()