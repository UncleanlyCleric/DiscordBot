from utils.spotify import get_spotify_track
from utils.apple import get_apple_track


async def resolve_music(query: str) -> str:

    # 🎧 Spotify
    if "spotify.com" in query:
        track = get_spotify_track(query)
        if track:
            return f"{track['name']} {track['artists'][0]['name']}"

    # 🍎 Apple Music
    if "music.apple.com" in query:
        track = await get_apple_track(query)
        if track:
            return f"{track['trackName']} {track['artistName']}"

    return query