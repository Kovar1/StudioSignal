"""Read-only movie discovery.

Collects candidate movie IDs from several TMDb list endpoints, deduplicates
them while preserving discovery order, and caps the total. This module does
NOT write to the database and does NOT ingest the discovered movies.
"""
from dataclasses import dataclass

from src.ingestion.tmdb_client import get_json


def _movie_ids(payload):
    """Extract ordered movie ids from a TMDb list-style response."""
    return [item["id"] for item in payload.get("results", []) if "id" in item]


def get_trending_movie_ids(page=1):
    return _movie_ids(get_json("/trending/movie/day", {"page": page}))


def get_popular_movie_ids(page=1):
    return _movie_ids(get_json("/movie/popular", {"page": page}))


def get_upcoming_movie_ids(page=1):
    return _movie_ids(get_json("/movie/upcoming", {"page": page}))


def get_now_playing_movie_ids(page=1):
    return _movie_ids(get_json("/movie/now_playing", {"page": page}))


@dataclass
class DiscoveryResult:
    ids: list[int]
    source_counts: dict[str, int]
    total_raw_ids: int
    total_unique_ids: int
    limit: int


def discover_movie_ids(limit=50, sources=None):
    """Collect, dedupe (order-preserving), and limit movie ids across sources.

    ``sources`` maps a source name to a zero-arg callable returning list[int];
    it defaults to the four real TMDb endpoints. It is injectable so the
    combine/dedupe/limit logic can be tested without network access.
    """
    if sources is None:
        sources = {
            "trending": get_trending_movie_ids,
            "popular": get_popular_movie_ids,
            "upcoming": get_upcoming_movie_ids,
            "now_playing": get_now_playing_movie_ids,
        }

    source_counts = {}
    combined = []
    for name, fetch_ids in sources.items():
        ids = fetch_ids()
        source_counts[name] = len(ids)
        combined.extend(ids)

    unique_ordered = list(dict.fromkeys(combined))

    return DiscoveryResult(
        ids=unique_ordered[:limit],
        source_counts=source_counts,
        total_raw_ids=len(combined),
        total_unique_ids=len(unique_ordered),
        limit=limit,
    )


def format_discovery_summary(result):
    """Render a DiscoveryResult as a clean printable string."""
    lines = ["Discovery complete.", "", "Sources checked:", ""]
    for name, count in result.source_counts.items():
        lines.append(f"* {name}: {count} IDs")

    lines += [
        "",
        f"Total raw IDs: {result.total_raw_ids}",
        f"Unique movie IDs: {result.total_unique_ids}",
        f"Limited to: {result.limit}",
        "",
        "Movie IDs:",
        ", ".join(str(movie_id) for movie_id in result.ids),
    ]
    return "\n".join(lines)
