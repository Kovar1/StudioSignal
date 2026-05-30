"""End-to-end (mocked) proof that one movie populates every table.

No live API calls: tmdb_client._request is monkeypatched to return a fat
payload, and run_one_movie drives the full pipeline against the temp_db engine.
"""
import types

from sqlalchemy import func, select

from src.db import (
    api_pull_logs,
    movie_cast,
    movie_crew,
    movie_genres,
    movie_keywords,
    movie_watch_providers,
    movie_weekly_snapshots,
    movies,
    release_dates,
)
from src.ingestion import run_one_movie, tmdb_client

FAT_PAYLOAD = {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "release_date": "1999-10-15",
    "runtime": 139,
    "budget": 63000000,
    "revenue": 100853753,
    "original_language": "en",
    "popularity": 61.4,
    "vote_average": 8.4,
    "vote_count": 26000,
    "status": "Released",
    "homepage": "",
    "overview": "An insomniac and a soap salesman form an underground fight club.",
    "imdb_id": "tt0137523",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
    "credits": {
        "cast": [
            {"id": 819, "name": "Edward Norton", "character": "The Narrator", "order": 0},
            {"id": 287, "name": "Brad Pitt", "character": "Tyler Durden", "order": 1},
        ],
        "crew": [
            {"id": 7467, "name": "David Fincher", "department": "Directing", "job": "Director"},
        ],
    },
    "keywords": {"keywords": [{"id": 825, "name": "support group"}]},
    "watch/providers": {
        "results": {"US": {"flatrate": [{"provider_id": 8, "provider_name": "Netflix"}]}}
    },
    "release_dates": {
        "results": [
            {
                "iso_3166_1": "US",
                "release_dates": [
                    {
                        "certification": "R",
                        "release_date": "1999-10-15T00:00:00.000Z",
                        "type": 3,
                        "note": "",
                    }
                ],
            }
        ]
    },
    "external_ids": {"imdb_id": "tt0137523"},
}


def _count(engine, table, where=None):
    stmt = select(func.count()).select_from(table)
    if where is not None:
        stmt = stmt.where(where)
    with engine.connect() as conn:
        return conn.execute(stmt).scalar_one()


def _patch_request(monkeypatch):
    fake = types.SimpleNamespace(status_code=200, json=lambda: FAT_PAYLOAD)
    monkeypatch.setattr(tmdb_client, "_request", lambda path, params=None: fake)


def test_one_movie_populates_every_table(temp_db, monkeypatch):
    _patch_request(monkeypatch)

    run_one_movie.run(550)

    assert _count(temp_db, movies, movies.c.movie_id == 550) == 1
    assert _count(temp_db, movie_weekly_snapshots, movie_weekly_snapshots.c.movie_id == 550) == 1
    assert _count(temp_db, api_pull_logs) == 1
    assert _count(temp_db, movie_genres, movie_genres.c.movie_id == 550) == 2
    assert _count(temp_db, movie_cast, movie_cast.c.movie_id == 550) == 2
    assert _count(temp_db, movie_crew, movie_crew.c.movie_id == 550) == 1
    assert _count(temp_db, movie_keywords, movie_keywords.c.movie_id == 550) == 1
    assert _count(temp_db, movie_watch_providers, movie_watch_providers.c.movie_id == 550) == 1
    assert _count(temp_db, release_dates, release_dates.c.movie_id == 550) == 1


def test_reingest_does_not_duplicate_enrichment(temp_db, monkeypatch):
    _patch_request(monkeypatch)

    run_one_movie.run(550)
    run_one_movie.run(550)

    # Movie + enrichment links are idempotent under re-ingest.
    assert _count(temp_db, movies, movies.c.movie_id == 550) == 1
    assert _count(temp_db, movie_genres, movie_genres.c.movie_id == 550) == 2
    assert _count(temp_db, movie_cast, movie_cast.c.movie_id == 550) == 2
    assert _count(temp_db, movie_crew, movie_crew.c.movie_id == 550) == 1
    assert _count(temp_db, movie_keywords, movie_keywords.c.movie_id == 550) == 1
    assert _count(temp_db, movie_watch_providers, movie_watch_providers.c.movie_id == 550) == 1
    assert _count(temp_db, release_dates, release_dates.c.movie_id == 550) == 1
    # Snapshots are point-in-time and intentionally accumulate per run.
    assert _count(temp_db, movie_weekly_snapshots, movie_weekly_snapshots.c.movie_id == 550) == 2
