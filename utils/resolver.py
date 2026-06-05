from utils.apple import get_apple_track


YOUTUBE_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "www.youtube.com",
    "m.youtube.com",
)


APPLE_DOMAINS = (
    "music.apple.com",
)


def is_youtube_url(query: str) -> bool:
    return any(domain in query for domain in YOUTUBE_DOMAINS)


def is_apple_url(query: str) -> bool:
    return any(domain in query for domain in APPLE_DOMAINS)


async def resolve_music(query: str) -> str:
    """
    Universal resolver for Wavelink/Lavalink bots.

    Converts supported music URLs into a format
    suitable for Playable.search().
    """

    query = query.strip()

    # 🎬 YouTube → pass through directly (IMPORTANT: no search conversion)
    # Wavelink/Lavalink handles YouTube URLs natively
    if is_youtube_url(query):
        return query

    # 🍎 Apple Music → convert to searchable text
    if is_apple_url(query):
        try:
            track = await get_apple_track(query)

            if track:
                title = track.get("title")
                artist = track.get("artist")

                if title and artist:
                    return f"{title} {artist}"

        except Exception:
            pass

    # 🎧 fallback → treat as search query
    return query