import re
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup


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
        # Lavalink handles playlist URLs directly
        return [url]

    # ---------------- APPLE MUSIC (FIXED) ----------------
    async def _apple(self, url: str):
        """
        Improved Apple Music resolver:
        - tries to extract playlist title from HTML
        - falls back to URL parsing if blocked
        """

        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            html = requests.get(url, headers=headers, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            # Try extracting real title
            title = soup.title.string if soup.title else ""

            if title:
                title = re.sub(r"-.*Apple Music.*", "", title).strip()
                title = re.sub(r"\s+", " ", title)

                if title:
                    return [title]

        except Exception as e:
            print("[APPLE PARSE FAIL]", e)

        # ---------------- FALLBACK (URL BASED) ----------------
        parsed = urlparse(url)
        path = unquote(parsed.path)

        path = re.sub(r"playlist|album|music|apple|com", "", path, flags=re.I)

        tokens = [t for t in path.split("/") if t]

        queries = []

        for t in tokens:
            cleaned = re.sub(r"[-_]+", " ", t).strip()
            cleaned = re.sub(r"\s+", " ", cleaned)

            if len(cleaned) > 2:
                queries.append(cleaned)

        # final safety fallback
        if not queries:
            fallback = url.split("/")[-1].replace("-", " ").strip()
            queries = [fallback]

        return queries

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\.", "", cleaned)
        cleaned = cleaned.replace("/", " ").strip()
        return cleaned