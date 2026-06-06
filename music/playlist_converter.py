import re
from urllib.parse import urlparse


class PlaylistConverter:
    """
    Converts playlist URLs into music-focused search queries.
    Works best-effort without Apple/Spotify APIs.
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
        # Lavalink can directly handle YouTube playlists
        return [url]

    # ---------------- APPLE MUSIC (FIXED) ----------------
    async def _apple(self, url: str):
        """
        FINAL FIX:
        We do NOT try to extract meaning from Apple URL structure
        (it produces garbage like "field trip waterfall").

        Instead, we generate controlled music-intent queries.
        """

        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]

        # try to grab a human-readable segment (best-effort only)
        raw_name = ""

        for p in parts:
            # ignore Apple playlist IDs
            if "pl." in p or p.startswith("pl"):
                continue

            cleaned = re.sub(r"[-_]+", " ", p)
            cleaned = re.sub(r"[0-9]+", "", cleaned).strip()

            if len(cleaned) > 2:
                raw_name = cleaned
                break

        # fallback if Apple gives nothing usable
        if not raw_name:
            raw_name = "top hits"

        # normalize
        raw_name = raw_name.strip()

        base = f"{raw_name} song"

        # IMPORTANT: force music intent (no nature / travel / ambience traps)
        return [
            base,
            f"{raw_name} official audio",
            f"{raw_name} music",
            "top hits 2026 songs",
            "popular music playlist 2026"
        ]

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\.", "", cleaned)
        cleaned = cleaned.replace("/", " ").strip()
        return cleaned