import asyncio
import logging
from typing import Dict, Optional

log = logging.getLogger(__name__)


class MediaResolver:
    """
    SAFE ASYNC MEDIA RESOLVER

    RULES:
    - NO discord imports
    - NO music manager imports
    - NO blocking calls in event loop
    """

    def __init__(self):
        self._ytdlp = None

    # ---------------------------
    # Lazy yt-dlp loader
    # ---------------------------

    def _get_ytdlp(self):
        if self._ytdlp is None:
            from yt_dlp import YoutubeDL

            self._ytdlp = YoutubeDL({
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "extract_flat": False,
                "default_search": "ytsearch",
            })

        return self._ytdlp

    # ---------------------------
    # Public API
    # ---------------------------

    async def resolve(self, query: str) -> Optional[Dict]:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._sync_resolve,
            query
        )

    # ---------------------------
    # Sync worker
    # ---------------------------

    def _sync_resolve(self, query: str) -> Optional[Dict]:
        ytdlp = self._get_ytdlp()

        try:
            if not query.startswith(("http://", "https://")):
                query = f"ytsearch1:{query}"

            info = ytdlp.extract_info(
                query,
                download=False
            )

            if "entries" in info:
                entries = list(info.get("entries", []))

                if not entries:
                    return None

                info = entries[0]

            return {
                "title": info.get("title"),
                "url": info.get("url"),
                "webpage_url": info.get("webpage_url"),
                "duration": info.get("duration"),
            }

        except Exception:
            log.exception(
                "Resolver failed for query=%s",
                query
            )
            return None


resolver = MediaResolver()