import re
from urllib.parse import urlparse


class PlaylistConverter:
    """
    Converts playlist URLs into SAFE YouTube search queries.
    Never returns URLs — ONLY text queries.
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
            return [url]  # safe: Lavalink handles playlists

        if source == "apple":
            return await self._apple(url)

        return [self._fallback(url)]

    # ---------------- APPLE MUSIC ----------------
    async def _apple(self, url: str):
        """
        Apple Music has no public API.
        We generate ONLY safe search queries.
        """

        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]

        name = None

        for p in parts:
            if "pl." in p or p.startswith("pl"):
                continue

            cleaned = re.sub(r"[-_]+", " ", p)
            cleaned = re.sub(r"[0-9]+", "", cleaned).strip()

            if len(cleaned) > 2:
                name = cleaned
                break

        if not name:
            name = "pop songs"

        name = name.strip()

        # 🚨 MUST be search-only text (NO URLs, NO playlist words)
        return [
            f"{name} official audio",
            f"{name} song",
            f"{name} music",
            f"{name} topic"
        ]

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\.", "", cleaned)
        cleaned = cleaned.replace("/", " ").strip()
        return cleaned