from datetime import date

from sqlalchemy import select

from src.db import movie_weekly_snapshots
from src.loaders.movie_loader import insert_weekly_snapshot


def _rows(engine):
    with engine.connect() as conn:
        return conn.execute(select(movie_weekly_snapshots)).mappings().all()


FULL_MOVIE = {
    "movie_id": 550,
    "popularity": 61.4,
    "vote_average": 8.4,
    "vote_count": 26000,
    "revenue": 100853753,
    "budget": 63000000,
    "status": "Released",
    "release_date": "1999-10-15",
    "runtime": 139,
    "original_language": "en",
    "imdb_id": "tt0137523",
}


def test_snapshot_includes_new_fields(temp_db):
    insert_weekly_snapshot(FULL_MOVIE, snapshot_date=date(2026, 5, 29))
    rows = _rows(temp_db)
    assert len(rows) == 1
    row = rows[0]
    assert row["snapshot_date"] == date(2026, 5, 29)
    assert row["movie_id"] == 550
    assert row["popularity"] == 61.4
    assert row["vote_average"] == 8.4
    assert row["vote_count"] == 26000
    assert row["revenue"] == 100853753
    assert row["budget"] == 63000000
    assert row["status"] == "Released"
    assert row["release_date"] == "1999-10-15"
    assert row["runtime"] == 139
    assert row["original_language"] == "en"
    assert row["imdb_id"] == "tt0137523"


def test_missing_fields_default_to_null(temp_db):
    # Only the required movie_id is supplied; every metric should be NULL-safe.
    insert_weekly_snapshot({"movie_id": 999})
    rows = _rows(temp_db)
    assert len(rows) == 1
    row = rows[0]
    assert row["movie_id"] == 999
    for col in (
        "popularity",
        "vote_average",
        "vote_count",
        "revenue",
        "budget",
        "status",
        "release_date",
        "runtime",
        "original_language",
        "imdb_id",
    ):
        assert row[col] is None
    # snapshot_date is never null; it defaults to today.
    assert row["snapshot_date"] == date.today()


def test_repeated_ingestion_appends_rows(temp_db):
    # Snapshots are historical and append-only: a second insert must add a row,
    # never overwrite the first.
    id1 = insert_weekly_snapshot(FULL_MOVIE)
    id2 = insert_weekly_snapshot(FULL_MOVIE)
    rows = _rows(temp_db)
    assert len(rows) == 2
    assert id1 != id2
    assert all(r["movie_id"] == 550 for r in rows)


def test_explicit_snapshot_date_preserved_across_runs(temp_db):
    insert_weekly_snapshot(FULL_MOVIE, snapshot_date=date(2026, 5, 22))
    insert_weekly_snapshot(FULL_MOVIE, snapshot_date=date(2026, 5, 29))
    dates = sorted(r["snapshot_date"] for r in _rows(temp_db))
    assert dates == [date(2026, 5, 22), date(2026, 5, 29)]
