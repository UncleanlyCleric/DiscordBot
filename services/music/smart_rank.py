import re
from typing import List


BAD_WORDS = [
    "live", "remix", "cover", "instrumental", "sped up", "slowed"
]


def score_track(title: str, query: str) -> float:
    """
    Simple production-grade heuristic scorer.
    """

    title_l = title.lower()
    query_l = query.lower()

    score = 0.0

    # exact match boost
    if query_l in title_l:
        score += 5

    # word overlap
    query_words = set(query_l.split())
    title_words = set(title_l.split())

    score += len(query_words & title_words) * 1.5

    # penalize bad variants
    for bad in BAD_WORDS:
        if bad in title_l:
            score -= 2

    # prefer official-like results
    if "official" in title_l:
        score += 1.5

    return score


def pick_best(results, query: str):
    """
    Returns best ranked result instead of raw first result.
    """

    ranked = sorted(
        results,
        key=lambda t: score_track(getattr(t, "title", ""), query),
        reverse=True
    )

    return ranked[0] if ranked else None