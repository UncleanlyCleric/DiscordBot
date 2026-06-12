from typing import List


BAD_WORDS = [
    "live", "remix", "cover", "instrumental", "sped up", "slowed"
]


def score_track(title: str, author: str, query: str) -> float:
    """
    Improved scorer with ARTIST awareness.
    """

    title_l = (title or "").lower()
    author_l = (author or "").lower()
    query_l = query.lower()

    score = 0.0

    # =====================================================
    # 🎯 HARD ARTIST MATCH (MOST IMPORTANT FIX)
    # =====================================================

    if author_l and author_l in query_l:
        score += 20

    if query_l in author_l:
        score += 15

    # =====================================================
    # TITLE MATCHING
    # =====================================================

    if query_l in title_l:
        score += 5

    # word overlap
    query_words = set(query_l.split())
    title_words = set(title_l.split())

    score += len(query_words & title_words) * 1.5

    # =====================================================
    # PENALIZE BAD VERSIONS
    # =====================================================

    for bad in BAD_WORDS:
        if bad in title_l:
            score -= 2

    # prefer official
    if "official" in title_l:
        score += 1.5

    return score


def pick_best(results, query: str):
    """
    Returns best ranked result instead of raw first result.
    """

    ranked = sorted(
        results,
        key=lambda t: score_track(
            getattr(t, "title", ""),
            getattr(t, "author", ""),
            query
        ),
        reverse=True
    )

    return ranked[0] if ranked else None