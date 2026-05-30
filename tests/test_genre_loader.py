from sqlalchemy import select

from src.db import genres, movie_genres
from src.loaders.genre_loader import load_genres


def _rows(engine, table):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


def test_inserts_genres_and_links(temp_db):
    count = load_genres(
        550, [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]
    )
    assert count == 2
    assert len(_rows(temp_db, genres)) == 2
    links = _rows(temp_db, movie_genres)
    assert len(links) == 2
    assert {link["movie_id"] for link in links} == {550}


def test_shared_genre_reused_across_movies(temp_db):
    load_genres(550, [{"id": 18, "name": "Drama"}])
    load_genres(680, [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}])
    # Drama's dimension row is created once and reused.
    assert len(_rows(temp_db, genres)) == 2
    assert len(_rows(temp_db, movie_genres)) == 3


def test_reingest_is_idempotent(temp_db):
    payload = [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]
    load_genres(550, payload)
    load_genres(550, payload)
    assert len(_rows(temp_db, genres)) == 2
    assert len(_rows(temp_db, movie_genres)) == 2


def test_duplicate_within_payload_collapsed(temp_db):
    count = load_genres(550, [{"id": 18, "name": "Drama"}, {"id": 18, "name": "Drama"}])
    assert count == 1
    assert len(_rows(temp_db, movie_genres)) == 1


def test_empty_and_missing_handled_safely(temp_db):
    assert load_genres(550, []) == 0
    assert load_genres(550, None) == 0
    assert load_genres(550, [{"name": "no id"}]) == 0
    assert len(_rows(temp_db, movie_genres)) == 0
