"""Tests for snapshot trend analytics.

Data is seeded directly into an isolated SQLite database (the autouse `temp_db`
fixture), so nothing here touches TMDb or the real dev/Supabase database.
"""
from datetime import date

import pytest
from sqlalchemy import insert

from src.analytics.snapshot_analytics import (
    get_movie_popularity_changes,
    get_top_popularity_decliners,
    get_top_popularity_gainers,
)
from src.db import movie_weekly_snapshots, movies


def _add_movie(engine, movie_id, title="Untitled"):
    with engine.begin() as conn:
        conn.execute(insert(movies).values(movie_id=movie_id, title=title))


def _add_snapshot(engine, movie_id, snapshot_date, popularity):
    with engine.begin() as conn:
        conn.execute(
            insert(movie_weekly_snapshots).values(
                movie_id=movie_id,
                snapshot_date=snapshot_date,
                popularity=popularity,
            )
        )


def _seed_two(engine, movie_id, title, previous_pop, latest_pop):
    """A movie with exactly two snapshots: an older one, then a newer one."""
    _add_movie(engine, movie_id, title)
    _add_snapshot(engine, movie_id, date(2026, 5, 1), previous_pop)
    _add_snapshot(engine, movie_id, date(2026, 5, 8), latest_pop)


def _by_id(records):
    return {r["movie_id"]: r for r in records}


def test_positive_popularity_growth(temp_db):
    _seed_two(temp_db, 1, "Riser", previous_pop=10.0, latest_pop=15.0)

    changes = _by_id(get_movie_popularity_changes())
    assert set(changes) == {1}
    c = changes[1]
    assert c["title"] == "Riser"
    assert c["latest_snapshot_date"] == date(2026, 5, 8)
    assert c["previous_snapshot_date"] == date(2026, 5, 1)
    assert c["latest_popularity"] == 15.0
    assert c["previous_popularity"] == 10.0
    assert c["popularity_delta"] == 5.0
    assert c["popularity_pct_change"] == pytest.approx(50.0)


def test_negative_popularity_growth(temp_db):
    _seed_two(temp_db, 2, "Faller", previous_pop=20.0, latest_pop=10.0)

    c = _by_id(get_movie_popularity_changes())[2]
    assert c["popularity_delta"] == -10.0
    assert c["popularity_pct_change"] == pytest.approx(-50.0)


def test_three_snapshots_use_latest_two_only(temp_db):
    _add_movie(temp_db, 3, "Trender")
    _add_snapshot(temp_db, 3, date(2026, 5, 1), 5.0)    # oldest -> must be ignored
    _add_snapshot(temp_db, 3, date(2026, 5, 8), 10.0)   # previous
    _add_snapshot(temp_db, 3, date(2026, 5, 15), 15.0)  # latest

    c = _by_id(get_movie_popularity_changes())[3]
    assert c["latest_snapshot_date"] == date(2026, 5, 15)
    assert c["previous_snapshot_date"] == date(2026, 5, 8)
    assert c["latest_popularity"] == 15.0
    assert c["previous_popularity"] == 10.0
    # delta is latest - previous (15 - 10), NOT latest - oldest (15 - 5)
    assert c["popularity_delta"] == 5.0


def test_single_snapshot_movie_excluded(temp_db):
    _add_movie(temp_db, 4, "Newcomer")
    _add_snapshot(temp_db, 4, date(2026, 5, 8), 12.0)  # only one snapshot
    _seed_two(temp_db, 5, "Established", previous_pop=8.0, latest_pop=9.0)

    changes = _by_id(get_movie_popularity_changes())
    assert 4 not in changes
    assert 5 in changes


def test_percent_change_calculation(temp_db):
    _seed_two(temp_db, 6, "Quarter", previous_pop=8.0, latest_pop=10.0)

    c = _by_id(get_movie_popularity_changes())[6]
    assert c["popularity_delta"] == 2.0
    assert c["popularity_pct_change"] == pytest.approx(25.0)  # 2 / 8 * 100


def test_gainers_and_decliners_ranking(temp_db):
    _seed_two(temp_db, 10, "A", previous_pop=100.0, latest_pop=130.0)  # delta +30
    _seed_two(temp_db, 11, "B", previous_pop=100.0, latest_pop=110.0)  # delta +10
    _seed_two(temp_db, 12, "C", previous_pop=100.0, latest_pop=95.0)   # delta  -5
    _seed_two(temp_db, 13, "D", previous_pop=100.0, latest_pop=75.0)   # delta -25
    # A single-snapshot movie must never appear in either ranking.
    _add_movie(temp_db, 14, "Loner")
    _add_snapshot(temp_db, 14, date(2026, 5, 8), 50.0)

    gainers = get_top_popularity_gainers()
    decliners = get_top_popularity_decliners()

    assert [r["movie_id"] for r in gainers] == [10, 11, 12, 13]
    assert [r["movie_id"] for r in decliners] == [13, 12, 11, 10]
    assert 14 not in [r["movie_id"] for r in gainers]
    assert 14 not in [r["movie_id"] for r in decliners]

    # limit is respected
    assert [r["movie_id"] for r in get_top_popularity_gainers(limit=2)] == [10, 11]
    assert [r["movie_id"] for r in get_top_popularity_decliners(limit=2)] == [13, 12]


def test_no_snapshots_returns_empty(temp_db):
    assert get_movie_popularity_changes() == []
    assert get_top_popularity_gainers() == []
    assert get_top_popularity_decliners() == []
