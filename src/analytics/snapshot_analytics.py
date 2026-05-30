"""Trend analytics over the weekly snapshot history.

These functions are read-only and work entirely from data already stored in the
database (`movies` + `movie_weekly_snapshots`). They never call TMDb and never
write anything. The first metric is *popularity momentum*: how each movie's
`popularity` changed between its two most recent weekly snapshots.

Both SQLite (local) and Postgres (Supabase) are supported -- the query is plain
SQLAlchemy Core and the "newest two snapshots per movie" selection is done in
Python, so no database-specific SQL features are involved.
"""
from collections import defaultdict

from sqlalchemy import select

from src.db import get_engine, movie_weekly_snapshots, movies


def _compute_change(latest_popularity, previous_popularity):
    """Return (delta, pct_change) for two popularity values.

    ``delta`` is None if either value is missing. ``pct_change`` is None when it
    cannot be computed -- a missing value, or a zero baseline that would divide
    by zero.
    """
    if latest_popularity is None or previous_popularity is None:
        return None, None
    delta = latest_popularity - previous_popularity
    if previous_popularity == 0:
        return delta, None
    return delta, delta / previous_popularity * 100


def _snapshots_newest_first():
    """Fetch snapshot rows (with movie title) ordered newest-first per movie.

    Ordered by movie_id, then snapshot_date descending, then snapshot_id
    descending, so that same-date snapshots fall back to insertion order (a
    later insert is treated as the newer snapshot).
    """
    s = movie_weekly_snapshots
    stmt = (
        select(
            s.c.movie_id,
            movies.c.title,
            s.c.snapshot_date,
            s.c.snapshot_id,
            s.c.popularity,
        )
        .select_from(s.outerjoin(movies, s.c.movie_id == movies.c.movie_id))
        .order_by(s.c.movie_id, s.c.snapshot_date.desc(), s.c.snapshot_id.desc())
    )
    with get_engine().connect() as conn:
        return conn.execute(stmt).mappings().all()


def get_movie_popularity_changes():
    """One popularity-change record per movie that has at least two snapshots.

    Each record compares the newest snapshot against the one immediately
    preceding it. Movies with fewer than two snapshots are skipped. Returns a
    list of dicts with: movie_id, title, latest_snapshot_date,
    previous_snapshot_date, latest_popularity, previous_popularity,
    popularity_delta, popularity_pct_change.
    """
    by_movie = defaultdict(list)
    for row in _snapshots_newest_first():
        by_movie[row["movie_id"]].append(row)

    changes = []
    for movie_id, snaps in by_movie.items():
        if len(snaps) < 2:
            continue
        latest, previous = snaps[0], snaps[1]
        delta, pct = _compute_change(latest["popularity"], previous["popularity"])
        changes.append(
            {
                "movie_id": movie_id,
                "title": latest["title"],
                "latest_snapshot_date": latest["snapshot_date"],
                "previous_snapshot_date": previous["snapshot_date"],
                "latest_popularity": latest["popularity"],
                "previous_popularity": previous["popularity"],
                "popularity_delta": delta,
                "popularity_pct_change": pct,
            }
        )
    return changes


def get_top_popularity_gainers(limit=10):
    """Movies ranked by highest popularity_delta first, capped at ``limit``.

    Movies whose delta can't be computed (missing popularity) are excluded.
    Ties break by movie_id ascending for a deterministic order.
    """
    ranked = [
        c for c in get_movie_popularity_changes() if c["popularity_delta"] is not None
    ]
    ranked.sort(key=lambda c: (-c["popularity_delta"], c["movie_id"]))
    return ranked[:limit]


def get_top_popularity_decliners(limit=10):
    """Movies ranked by lowest popularity_delta first, capped at ``limit``.

    Movies whose delta can't be computed (missing popularity) are excluded.
    Ties break by movie_id ascending for a deterministic order.
    """
    ranked = [
        c for c in get_movie_popularity_changes() if c["popularity_delta"] is not None
    ]
    ranked.sort(key=lambda c: (c["popularity_delta"], c["movie_id"]))
    return ranked[:limit]
