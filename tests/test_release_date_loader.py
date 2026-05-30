from sqlalchemy import select

from src.db import release_dates
from src.loaders.release_date_loader import load_release_dates


def _rows(engine):
    with engine.connect() as conn:
        return conn.execute(select(release_dates)).mappings().all()


PAYLOAD = {
    "results": [
        {
            "iso_3166_1": "US",
            "release_dates": [
                {
                    "certification": "R",
                    "release_date": "1999-10-15T00:00:00.000Z",
                    "type": 3,
                    "note": "",
                },
                {
                    "certification": "R",
                    "release_date": "2000-06-06T00:00:00.000Z",
                    "type": 5,
                    "note": "DVD",
                },
            ],
        },
        {
            "iso_3166_1": "GB",
            "release_dates": [
                {
                    "certification": "18",
                    "release_date": "1999-11-12T00:00:00.000Z",
                    "type": 3,
                    "note": "",
                }
            ],
        },
    ]
}


def test_inserts_rows(temp_db):
    count = load_release_dates(550, PAYLOAD)
    assert count == 3
    rows = _rows(temp_db)
    assert len(rows) == 3
    us = [r for r in rows if r["country_code"] == "US"]
    assert len(us) == 2
    assert {r["release_type"] for r in us} == {3, 5}
    dvd = [r for r in us if r["note"] == "DVD"]
    assert dvd and dvd[0]["release_type"] == 5


def test_reingest_is_idempotent(temp_db):
    load_release_dates(550, PAYLOAD)
    load_release_dates(550, PAYLOAD)
    assert len(_rows(temp_db)) == 3


def test_reingest_only_replaces_target_movie(temp_db):
    load_release_dates(550, PAYLOAD)
    load_release_dates(
        680,
        {
            "results": [
                {
                    "iso_3166_1": "US",
                    "release_dates": [
                        {
                            "certification": "R",
                            "release_date": "1994-10-14T00:00:00.000Z",
                            "type": 3,
                        }
                    ],
                }
            ]
        },
    )
    load_release_dates(550, PAYLOAD)  # re-ingesting 550 must not touch 680
    rows = _rows(temp_db)
    assert len([r for r in rows if r["movie_id"] == 550]) == 3
    assert len([r for r in rows if r["movie_id"] == 680]) == 1


def test_empty_and_missing_handled_safely(temp_db):
    assert load_release_dates(550, {}) == 0
    assert load_release_dates(550, None) == 0
    assert load_release_dates(550, {"results": []}) == 0
    assert len(_rows(temp_db)) == 0
