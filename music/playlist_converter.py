import re
from urllib.parse import urlparse, unquote


class PlaylistConverter:
    """
    Converts playlist URLs (Apple Music / YouTube / generic) into search queries.
    No external APIs required.
    """

    def detect_source(self, url: str):
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        if "music.apple.com" in url:
            return "apple"
        return "unknown"

    async def convert(self, url: str):
        source = self.detect_source(url)

        if source == "youtube":
            return await self._youtube(url)

        if source == "apple":
            return await self._apple(url)

        return [self._fallback(url)]

    # ---------------- YOUTUBE ----------------
    async def _youtube(self, url: str):
        # Lavalink can handle playlist URLs directly
        return [url]

    # ---------------- APPLE MUSIC ----------------
    async def _apple(self, url: str):
        """
        Apple Music has no open API for track extraction.
        We extract readable keywords from URL path.
        """

        parsed = urlparse(url)
        path = unquote(parsed.path)

        # remove noise words
        path = re.sub(r"playlist|album|music|apple|com", "", path, flags=re.I)

        # split into tokens
        tokens = [t for t in path.split("/") if t]

        if not tokens:
            return []

        # build search queries
        queries = []

        for t in tokens:
            cleaned = re.sub(r"[-_]+", " ", t).strip()
            if len(cleaned) > 2:
                queries.append(cleaned)

        return queries

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\\.", "", cleaned)
        return cleaned.replace("/", " ").strip()