"""End-to-end workflow: discovery -> ingestion.

Takes the movie IDs returned by discovery and runs each through the existing
ingestion pipeline (details -> raw storage -> transform -> upsert -> snapshot),
reusing the pipeline modules rather than reimplementing them. A failure on one
movie does not stop the run.

Run from the project root as a module:

    python -m src.ingestion.run_discovered_ingestion
"""
from dataclasses import dataclass

from src.db import init_db
from src.ingestion.discover_movies import discover_movie_ids
from src.ingestion.tmdb_client import get_movie_details
from src.loaders.enrichment import enrich_movie
from src.loaders.movie_loader import insert_weekly_snapshot, upsert_movie
from src.loaders.raw_loader import save_raw_response
from src.transforms.movie_transform import transform_movie_details


@dataclass
class MovieIngestionResult:
    """Outcome of attempting to ingest one discovered movie."""

    movie_id: int
    title: str | None = None
    raw_saved: bool = False
    upserted: bool = False
    snapshot_created: bool = False
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def ingest_movie(movie_id) -> MovieIngestionResult:
    """Run one discovered movie through the existing pipeline, isolating errors."""
    result = MovieIngestionResult(movie_id=movie_id)
    try:
        raw = get_movie_details(movie_id)
        save_raw_response("tmdb", f"/movie/{movie_id}", movie_id, raw)
        result.raw_saved = True

        movie = transform_movie_details(raw)
        result.title = movie.get("title")
        upsert_movie(movie)
        result.upserted = True

        enrich_movie(movie["movie_id"], raw)

        insert_weekly_snapshot(movie)
        result.snapshot_created = True
    except Exception as exc:  # isolate failure to this movie
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def summarize_discovered_ingestion(results, discovered=None) -> dict:
    """Reduce ingestion results to counts. Pure and network/DB-free.

    ``discovered`` is the number of ids handed to ingestion; it defaults to the
    number attempted when not supplied.
    """
    attempted = len(results)
    return {
        "discovered": attempted if discovered is None else discovered,
        "attempted": attempted,
        "succeeded": sum(1 for r in results if r.succeeded),
        "failed": sum(1 for r in results if not r.succeeded),
        "raw_saved": sum(1 for r in results if r.raw_saved),
        "upserted": sum(1 for r in results if r.upserted),
        "snapshots": sum(1 for r in results if r.snapshot_created),
    }


def format_discovered_ingestion_summary(results, discovered=None) -> str:
    """Render the discovered-ingestion summary. Pure and network/DB-free."""
    counts = summarize_discovered_ingestion(results, discovered)
    lines = [
        "Discovered ingestion complete.",
        "",
        f"Movies discovered: {counts['discovered']}",
        f"Movies attempted: {counts['attempted']}",
        f"Movies succeeded: {counts['succeeded']}",
        f"Movies failed: {counts['failed']}",
        "",
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


def run_discovered_ingestion(limit=20):
    """Discover up to ``limit`` movie ids and ingest each; print the summary."""
    init_db()
    discovery = discover_movie_ids(limit=limit)
    results = [ingest_movie(movie_id) for movie_id in discovery.ids]
    print(format_discovered_ingestion_summary(results, discovered=len(discovery.ids)))
    return results


def main():
    run_discovered_ingestion()


if __name__ == "__main__":
    main()
