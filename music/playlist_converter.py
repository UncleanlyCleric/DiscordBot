import re
from urllib.parse import urlparse


class PlaylistConverter:
    """
    Converts playlist URLs (Apple Music / YouTube / generic)
    into search queries for Lavalink (YouTube fallback).
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
        # Lavalink can handle playlists directly
        return [url]

    # ---------------- APPLE MUSIC (FIXED) ----------------
    async def _apple(self, url: str):
        """
        Apple Music cannot be reliably scraped.
        We convert the URL into multiple strong YouTube search seeds.
        """

        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]

        seed_parts = []

        for p in parts:
            # skip Apple playlist IDs like pl.u-xxxx
            if p.startswith("pl.") or "pl." in p:
                continue

            cleaned = re.sub(r"[-_]+", " ", p)
            cleaned = re.sub(r"[0-9]+", "", cleaned).strip()

            if len(cleaned) > 2:
                seed_parts.append(cleaned)

        # fallback if Apple gives nothing useful
        if not seed_parts:
            seed_parts = [parts[-2]] if len(parts) >= 2 else [url]

        base = " ".join(seed_parts).strip()

        # IMPORTANT: expand into multiple queries (this is what makes it work)
        return [
            base,
            f"{base} playlist",
            f"{base} mix",
            f"{base} songs"
        ]

    # ---------------- FALLBACK ----------------
    def _fallback(self, url: str):
        cleaned = re.sub(r"https?://", "", url)
        cleaned = re.sub(r"www\.", "", cleaned)
        cleaned = cleaned.replace("/", " ").strip()
        return cleaned