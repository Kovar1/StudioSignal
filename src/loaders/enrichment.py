"""Run every enrichment loader for one movie, isolating per-category failures.

This sits between the raw TMDb payload and the individual enrichment loaders:
it slices the payload and dispatches each slice to its loader. Each category is
wrapped independently so that a failure in one (say, watch providers) does not
prevent the others from loading, mirroring the per-movie error isolation the
ingestion entrypoints already use.
"""
from src.loaders.credit_loader import load_credits
from src.loaders.genre_loader import load_genres
from src.loaders.keyword_loader import load_keywords
from src.loaders.release_date_loader import load_release_dates
from src.loaders.watch_provider_loader import load_watch_providers


def enrich_movie(movie_id, raw_json):
    """Load all enrichment categories for ``movie_id`` from a raw movie payload.

    Returns a dict mapping each category to its outcome:
    ``{category: {"ok": bool, "result": <loader return>, "error": str | None}}``.
    A category whose loader raises is recorded with ``ok=False`` and the error
    text; it never propagates, so the caller's movie ingestion is unaffected.
    """
    raw_json = raw_json or {}
    loaders = {
        "genres": lambda: load_genres(movie_id, raw_json.get("genres")),
        "credits": lambda: load_credits(movie_id, raw_json.get("credits")),
        "keywords": lambda: load_keywords(movie_id, raw_json.get("keywords")),
        "watch_providers": lambda: load_watch_providers(
            movie_id, raw_json.get("watch/providers")
        ),
        "release_dates": lambda: load_release_dates(
            movie_id, raw_json.get("release_dates")
        ),
    }

    outcomes = {}
    for name, run_loader in loaders.items():
        try:
            outcomes[name] = {"ok": True, "result": run_loader(), "error": None}
        except Exception as exc:  # isolate failure to this enrichment category
            outcomes[name] = {
                "ok": False,
                "result": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
    return outcomes
