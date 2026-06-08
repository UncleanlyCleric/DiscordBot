from typing import List, Optional

from services.music.models import Track


class MusicResolver:
    """
    Converts:
    - URLs (YouTube, SoundCloud, Apple Music placeholders, Spotify placeholders)
    - search strings

    into normalized Track objects.

    NOTE:
    Actual streaming extraction (yt-dlp / lavalink plugins)
    will be plugged in later.
    """

    # -------------------------
    # ENTRY POINT
    # -------------------------

    async def resolve(self, query: str, requester_id: int) -> List[Track]:
        query = query.strip()

        if not query:
            return []

        # URL vs search
        if self._is_url(query):
            return await self._resolve_url(query, requester_id)

        return await self._search(query, requester_id)

    # -------------------------
    # URL DETECTION
    # -------------------------

    def _is_url(self, query: str) -> bool:
        return query.startswith("http://") or query.startswith("https://")

    # -------------------------
    # URL RESOLUTION
    # -------------------------

    async def _resolve_url(self, url: str, requester_id: int) -> List[Track]:
        """
        Placeholder resolver.

        Later we will integrate:
        - yt-dlp (YouTube, SoundCloud, Apple Music metadata extraction)
        - Lavalink plugins (Spotify / Apple Music via search mapping)
        """

        # YouTube
        if "youtube.com" in url or "youtu.be" in url:
            return [Track(
                title="YouTube Track",
                author=None,
                uri=url,
                source="youtube",
                requester_id=requester_id
            )]

        # SoundCloud
        if "soundcloud.com" in url:
            return [Track(
                title="SoundCloud Track",
                author=None,
                uri=url,
                source="soundcloud",
                requester_id=requester_id
            )]

        # Apple Music (placeholder mapping)
        if "music.apple.com" in url:
            return [Track(
                title="Apple Music Track",
                author=None,
                uri=url,
                source="apple_music",
                requester_id=requester_id
            )]

        # Spotify (cannot stream directly)
        if "spotify.com" in url:
            return [Track(
                title="Spotify Track (mapped)",
                author=None,
                uri=url,
                source="spotify",
                requester_id=requester_id
            )]

        # fallback
        return [Track(
            title="Unknown Track",
            author=None,
            uri=url,
            source="unknown",
            requester_id=requester_id
        )]

    # -------------------------
    # SEARCH RESOLUTION
    # -------------------------

    async def _search(self, query: str, requester_id: int) -> List[Track]:
        """
        Placeholder search.

        Later we plug in:
        - YouTube search API (yt-dlp / ytsearch)
        - Lavalink search endpoint
        """

        return [Track(
            title=f"Search result for: {query}",
            author=None,
            uri=f"ytsearch:{query}",
            source="search",
            requester_id=requester_id
        )]


music_resolver = MusicResolver()