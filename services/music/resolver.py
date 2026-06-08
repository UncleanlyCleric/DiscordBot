from typing import List

import wavelink

from services.music.models import Track


class MusicResolver:
    """
    Resolve URLs and searches using Lavalink/Wavelink.

    Returns normalized Track objects populated with
    real metadata from the source.
    """

    async def resolve(
        self,
        query: str,
        requester_id: int
    ) -> List[Track]:

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

            for item in results.tracks:
                tracks.append(
                    Track(
                        title=item.title,
                        author=getattr(item, "author", None),
                        uri=item.uri,
                        source=str(getattr(item, "source", None)),
                        requester_id=requester_id,
                    )
                )

            return tracks

        # Search results / single tracks
        for item in results:

            tracks.append(
                Track(
                    title=item.title,
                    author=getattr(item, "author", None),
                    uri=item.uri,
                    source=str(getattr(item, "source", None)),
                    requester_id=requester_id,
                )
            )

        return tracks


music_resolver = MusicResolver()