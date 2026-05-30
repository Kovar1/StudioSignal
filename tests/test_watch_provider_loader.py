from sqlalchemy import select

from src.db import movie_watch_providers, watch_providers
from src.loaders.watch_provider_loader import load_watch_providers


def _rows(engine, table):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


PAYLOAD = {
    "results": {
        "US": {
            "link": "https://www.themoviedb.org/movie/550/watch",
            "flatrate": [{"provider_id": 8, "provider_name": "Netflix"}],
            "rent": [{"provider_id": 2, "provider_name": "Apple TV"}],
        },
        "GB": {
            "flatrate": [{"provider_id": 8, "provider_name": "Netflix"}],
        },
    }
}


def test_inserts_and_links(temp_db):
    count = load_watch_providers(550, PAYLOAD)
    assert count == 3  # US/flatrate, US/rent, GB/flatrate
    # Netflix(8) + Apple TV(2) -> two dimension rows, shared across countries.
    assert len(_rows(temp_db, watch_providers)) == 2
    links = _rows(temp_db, movie_watch_providers)
    access = {(link["country_code"], link["access_type"]) for link in links}
    assert access == {("US", "flatrate"), ("US", "rent"), ("GB", "flatrate")}


def test_link_string_is_ignored(temp_db):
    load_watch_providers(550, PAYLOAD)
    names = {p["provider_name"] for p in _rows(temp_db, watch_providers)}
    assert names == {"Netflix", "Apple TV"}


def test_reingest_is_idempotent(temp_db):
    load_watch_providers(550, PAYLOAD)
    load_watch_providers(550, PAYLOAD)
    assert len(_rows(temp_db, watch_providers)) == 2
    assert len(_rows(temp_db, movie_watch_providers)) == 3


def test_duplicate_within_payload_collapsed(temp_db):
    payload = {
        "results": {
            "US": {
                "flatrate": [
                    {"provider_id": 8, "provider_name": "Netflix"},
                    {"provider_id": 8, "provider_name": "Netflix"},
                ]
            }
        }
    }
    assert load_watch_providers(550, payload) == 1
    assert len(_rows(temp_db, movie_watch_providers)) == 1


def test_empty_and_missing_handled_safely(temp_db):
    assert load_watch_providers(550, {}) == 0
    assert load_watch_providers(550, None) == 0
    assert load_watch_providers(550, {"results": {}}) == 0
    assert len(_rows(temp_db, movie_watch_providers)) == 0
