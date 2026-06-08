import re
import aiohttp


APPLE_MUSIC_REGEX = r"music\.apple\.com/.*/album/|song/|playlist/"


class URLResolver:

    async def resolve(self, query: str) -> str:

        # -----------------------------
        # Apple Music URL handling
        # -----------------------------
        if re.search(APPLE_MUSIC_REGEX, query):

            return await self._resolve_apple_music(query)

        return query

    async def _resolve_apple_music(self, url: str) -> str:
        """
        Apple Music cannot be streamed directly.
        We extract metadata and convert to search query.
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()

            # extremely lightweight extraction (title fallback)
            # production bots use oEmbed or Apple API here
            title_match = re.search(r'"name":"([^"]+)"', html)

            if title_match:
                return title_match.group(1)

        except Exception:
            pass

        # fallback: brute force search key
        return "apple music track"
    

url_resolver = URLResolver()