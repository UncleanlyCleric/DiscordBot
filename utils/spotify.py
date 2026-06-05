import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))


def get_spotify_track(query: str):
    if "spotify.com/track" in query:
        track_id = query.split("/")[-1].split("?")[0]
        return sp.track(track_id)

    results = sp.search(q=query, type="track", limit=1)
    return results["tracks"]["items"][0] if results["tracks"]["items"] else None