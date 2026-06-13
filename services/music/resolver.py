import re
import logging
import wavelink

from services.music.models import Track
from services.music.smart_rank import pick_best

APPLE_MUSIC = r"music\.apple\.com"
SPOTIFY = r"open\.spotify\.com"

BAD_RESULTS = [
    "karaoke",
    "instrumental",
    "nightcore",
    "8d audio",
    "bass boosted",
    "sped up",
    "slowed",
    "reverb",
    "cover",
    "tribute",
    "reaction",
    "lyrics",
]


class MusicResolver:

    async def resolve(
        self,
        query: str,
        requester_id: int
    ):

        query = query.strip()

        if not query:
            return []

        is_url = (
            query.startswith("http")
            or re.search(APPLE_MUSIC, query)
            or re.search(SPOTIFY, query)
        )

        try:

            results = await wavelink.Playable.search(
                query
            )

            # ==========================================
            # Spotify fallback
            # ==========================================

            if (
                not results
                and re.search(SPOTIFY, query)
            ):

                logging.warning(
                    "[SPOTIFY] direct lookup failed, falling back"
                )

                try:

                    playlist_match = re.search(
                        r"playlist/([A-Za-z0-9]+)",
                        query
                    )

                    track_match = re.search(
                        r"track/([A-Za-z0-9]+)",
                        query
                    )

                    if playlist_match:

                        logging.warning(
                            "[SPOTIFY] playlist fallback not available without Spotify API credentials"
                        )

                        return []

                    elif track_match:

                        logging.info(
                            "[SPOTIFY] track fallback search"
                        )

                        spotify_id = track_match.group(1)

                        fallback_query = spotify_id

                        results = await wavelink.Playable.search(
                            fallback_query
                        )

                except Exception:

                    logging.exception(
                        "[SPOTIFY] fallback failed"
                    )

                    return []

            logging.info(
                "[SEARCH] query='%s' results=%s",
                query,
                len(results)
            )

            for i, track in enumerate(results[:10], start=1):

                logging.info(
                    "[SEARCH] #%s title='%s' author='%s'",
                    i,
                    getattr(track, "title", ""),
                    getattr(track, "author", "")
                )

        except Exception:

            logging.exception(
                "[SEARCH] failed query='%s'",
                query
            )

            return []

        if not results:

            logging.info(
                "[SEARCH] no results for '%s'",
                query
            )

            return []

        playlist = getattr(
            results,
            "playlist",
            None
        )

        if (
            playlist
            or isinstance(
                results,
                wavelink.Playlist
            )
        ):

            tracks = getattr(
                results,
                "tracks",
                results
            )

            logging.info(
                "[SEARCH] playlist returned tracks=%s",
                len(tracks)
            )

            return [
                Track(
                    title=t.title,
                    author=getattr(
                        t,
                        "author",
                        None
                    ),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                    artwork=getattr(
                        t,
                        "artwork",
                        None
                    ),
                )
                for t in tracks
            ]

        if is_url:

            return [
                Track(
                    title=t.title,
                    author=getattr(
                        t,
                        "author",
                        None
                    ),
                    uri=t.uri,
                    requester_id=requester_id,
                    playable=t,
                    artwork=getattr(
                        t,
                        "artwork",
                        None
                    ),
                )
                for t in results
            ]

        filtered = []

        for track in results:

            title = getattr(
                track,
                "title",
                ""
            ).lower()

            if any(
                bad in title
                for bad in BAD_RESULTS
            ):
                continue

            filtered.append(track)

        if filtered:
            results = filtered

        query_l = query.lower().strip()

        artist_search = (
            len(query_l.split()) <= 3
            and not any(
                x in query_l
                for x in [" - ", ":"]
            )
        )

        if artist_search:

            exact_artist_matches = [
                track
                for track in results
                if (
                    getattr(track, "author", "") or ""
                ).lower().strip() == query_l
            ]

            if exact_artist_matches:

                logging.info(
                    "[ARTIST_MATCH] found=%s artist='%s'",
                    len(exact_artist_matches),
                    query_l
                )

                best = exact_artist_matches[0]

                logging.info(
                    "[PICKED_ARTIST] title='%s' author='%s'",
                    getattr(best, "title", ""),
                    getattr(best, "author", "")
                )

                return [
                    Track(
                        title=best.title,
                        author=getattr(
                            best,
                            "author",
                            None
                        ),
                        uri=best.uri,
                        requester_id=requester_id,
                        playable=best,
                        artwork=getattr(
                            best,
                            "artwork",
                            None
                        ),
                    )
                ]

        def score(track):

            title = (
                getattr(track, "title", "") or ""
            ).lower()

            author = (
                getattr(track, "author", "") or ""
            ).lower()

            score = 0

            if author == query_l:
                score += 100

            if query_l in author:
                score += 50

            if query_l in title:
                score += 25

            query_words = set(
                query_l.split()
            )

            score += len(
                query_words &
                set(author.split())
            ) * 10

            score += len(
                query_words &
                set(title.split())
            ) * 5

            return score

        results = sorted(
            results,
            key=score,
            reverse=True
        )

        logging.info(
            "[RANKING] top candidates:"
        )

        for i, track in enumerate(results[:10], start=1):

            logging.info(
                "[RANKING] #%s score=%s title='%s' author='%s'",
                i,
                score(track),
                getattr(track, "title", ""),
                getattr(track, "author", "")
            )

        best = pick_best(
            results,
            query
        )

        if not best:
            return []

        logging.info(
            "[PICKED] title='%s' author='%s'",
            best.title,
            getattr(best, "author", "")
        )

        return [
            Track(
                title=best.title,
                author=getattr(
                    best,
                    "author",
                    None
                ),
                uri=best.uri,
                requester_id=requester_id,
                playable=best,
                artwork=getattr(
                    best,
                    "artwork",
                    None
                ),
            )
        ]


music_resolver = MusicResolver()