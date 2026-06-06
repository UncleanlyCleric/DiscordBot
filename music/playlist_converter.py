import re


class PlaylistConverter:
    """
    URLs are passed directly to Lavalink.
    Plain text is treated as a search query.
    """

    async def convert(self, query: str):

        if not query:
            return []

        query = query.strip()

        # URLs go directly to Lavalink
        if query.startswith("http://") or query.startswith("https://"):
            return [query]

        # Normal search text
        query = re.sub(r"\s+", " ", query)

        return [query]