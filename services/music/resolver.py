from typing import List

import wavelink

from services.music.models import Track


class MusicResolver:

    async def resolve(self, query: str, requester_id: int) -> List[Track]:

        query = query.strip()
        if not query:
            return []

        try:
            results = await wavelink.Playable.search(query)
        except Exception as e:
            print(f"[Resolver] Search failed: {e}")
            return []

        if not results:
            return []

        tracks: List[Track] = []

        # Playlist support
        if isinstance(results, wavelink.Playlist):
            items = results.tracks
        else:
            items = results

        for item in items:

            tracks.append(
                Track(
                    title=item.title,
                    author=getattr(item, "author", None),
                    uri=item.uri,

                    # 🔥 CRITICAL ADDITION
                    source="wavelink",
                    requester_id=requester_id,

                    # 👇 THIS IS THE FIX
                    _wavelink_track=item
                )
            )

        return tracks


music_resolver = MusicResolver()