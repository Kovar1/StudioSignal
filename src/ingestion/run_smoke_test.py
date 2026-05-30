"""Multi-movie smoke test for the ingestion pipeline.

Runs the existing single-movie flow across a handful of known TMDb IDs to
prove multi-movie ingestion works without breaking, duplicating movie rows,
or failing silently. One movie's failure does not stop the others.

Run from the project root as a module:

    python -m src.ingestion.run_smoke_test
"""
from dataclasses import dataclass

from src.db import init_db
from src.ingestion.tmdb_client import get_movie_details
from src.loaders.enrichment import enrich_movie
from src.loaders.movie_loader import insert_weekly_snapshot, upsert_movie
from src.loaders.raw_loader import save_raw_response
from src.transforms.movie_transform import transform_movie_details

# Known, stable TMDb ids: Fight Club, Inception, The Dark Knight,
# Pulp Fiction, Forrest Gump.
MOVIE_IDS = [550, 27205, 155, 680, 13]


@dataclass
class MovieResult:
    """Outcome of attempting to ingest a single movie."""

    movie_id: int
    raw_saved: bool = False
    upserted: bool = False
    snapshot_created: bool = False
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def ingest_movie(movie_id) -> MovieResult:
    """Run one movie through the full pipeline, capturing any failure.

    Each step flips its flag only after it completes, so the result reflects
    exactly how far a partially-failed movie got.
    """
    result = MovieResult(movie_id=movie_id)
    try:
        raw = get_movie_details(movie_id)
        save_raw_response("tmdb", f"/movie/{movie_id}", movie_id, raw)
        result.raw_saved = True

        movie = transform_movie_details(raw)
        upsert_movie(movie)
        result.upserted = True

        enrich_movie(movie["movie_id"], raw)

        insert_weekly_snapshot(movie)
        result.snapshot_created = True
    except Exception as exc:  # isolate failure to this movie
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def summarize(results) -> dict:
    """Reduce a list of MovieResult into counts. Pure and network-free."""
    return {
        "attempted": len(results),
        "succeeded": sum(1 for r in results if r.succeeded),
        "failed": sum(1 for r in results if not r.succeeded),
        "raw_saved": sum(1 for r in results if r.raw_saved),
        "upserted": sum(1 for r in results if r.upserted),
        "snapshots": sum(1 for r in results if r.snapshot_created),
    }


def format_summary(results) -> str:
    """Render the human-readable smoke-test summary. Pure and network-free."""
    counts = summarize(results)
    lines = [
        "Smoke test complete.",
        "",
        f"Movies attempted: {counts['attempted']}",
        f"Movies succeeded: {counts['succeeded']}",
        f"Movies failed: {counts['failed']}",
        f"Raw responses saved: {counts['raw_saved']}",
        f"Movies upserted: {counts['upserted']}",
        f"Weekly snapshots created: {counts['snapshots']}",
        "",
        "Failures:",
    ]

    failures = [r for r in results if not r.succeeded]
    if failures:
        lines.append("")
        for r in failures:
            lines.append(f"* movie_id={r.movie_id}: {r.error}")
    else:
        lines.append("None")

    return "\n".join(lines)


def run_smoke_test(movie_ids=MOVIE_IDS):
    """Ingest every id, print the summary, and return the per-movie results."""
    init_db()
    results = [ingest_movie(movie_id) for movie_id in movie_ids]
    print(format_summary(results))
    return results


def main():
    run_smoke_test()


if __name__ == "__main__":
    main()
