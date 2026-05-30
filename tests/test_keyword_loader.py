from sqlalchemy import select

from src.db import keywords, movie_keywords
from src.loaders.keyword_loader import load_keywords


def _rows(engine, table):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


PAYLOAD = {
    "keywords": [
        {"id": 825, "name": "support group"},
        {"id": 851, "name": "dual identity"},
    ]
}


def test_inserts_and_links(temp_db):
    assert load_keywords(550, PAYLOAD) == 2
    assert len(_rows(temp_db, keywords)) == 2
    assert len(_rows(temp_db, movie_keywords)) == 2


def test_shared_keyword_reused(temp_db):
    load_keywords(550, {"keywords": [{"id": 825, "name": "support group"}]})
    load_keywords(680, {"keywords": [{"id": 825, "name": "support group"}]})
    assert len(_rows(temp_db, keywords)) == 1
    assert len(_rows(temp_db, movie_keywords)) == 2


def test_reingest_is_idempotent(temp_db):
    load_keywords(550, PAYLOAD)
    load_keywords(550, PAYLOAD)
    assert len(_rows(temp_db, keywords)) == 2
    assert len(_rows(temp_db, movie_keywords)) == 2


def test_duplicate_within_payload_collapsed(temp_db):
    payload = {"keywords": [{"id": 825, "name": "x"}, {"id": 825, "name": "x"}]}
    assert load_keywords(550, payload) == 1
    assert len(_rows(temp_db, movie_keywords)) == 1


def test_empty_and_missing_handled_safely(temp_db):
    assert load_keywords(550, {}) == 0
    assert load_keywords(550, None) == 0
    assert load_keywords(550, {"keywords": []}) == 0
    assert len(_rows(temp_db, movie_keywords)) == 0
