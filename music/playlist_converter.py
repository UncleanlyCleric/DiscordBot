import re
from urllib.parse import urlparse


class PlaylistConverter:
    """
    Converts playlist URLs into STRICT music-track search queries.
    Designed to avoid "focus music / lofi / study mix" results.
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
        # Lavalink handles playlist directly
        return [url]

    # ---------------- APPLE MUSIC (FINAL FIX) ----------------
    async def _apple(self, url: str):
        """
        FINAL FIX:
        No playlist semantics.
        No generic music terms.
        ONLY track-level search intent.
        """

        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]

        name = None

        for p in parts:
            # skip Apple playlist IDs
            if "pl." in p or p.startswith("pl"):
                continue

            cleaned = re.sub(r"[-_]+", " ", p)
            cleaned = re.sub(r"[0-9]+", "", cleaned).strip()

            if len(cleaned) > 2:
                name = cleaned
                break

        # fallback safety
        if not name:
            name = "pop"

        name = name.strip()

        # 🔥 STRICT TRACK-LEVEL QUERIES ONLY
        return [
            f"{name} official audio",
            f"{name} song",
            f"{name} lyrics",
            f"{name} audio"
        ]

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\.", "", cleaned)
        cleaned = cleaned.replace("/", " ").strip()
        return cleaned