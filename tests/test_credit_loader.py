from sqlalchemy import select

from src.db import movie_cast, movie_crew, people
from src.loaders.credit_loader import load_credits


def _rows(engine, table):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


CREDITS = {
    "cast": [
        {"id": 819, "name": "Edward Norton", "character": "The Narrator", "order": 0},
        {"id": 287, "name": "Brad Pitt", "character": "Tyler Durden", "order": 1},
    ],
    "crew": [
        {"id": 7467, "name": "David Fincher", "department": "Directing", "job": "Director"},
        {"id": 7468, "name": "Jim Uhls", "department": "Writing", "job": "Screenplay"},
    ],
}


def test_inserts_people_and_links(temp_db):
    counts = load_credits(550, CREDITS)
    assert counts == {"cast": 2, "crew": 2}
    assert len(_rows(temp_db, people)) == 4
    assert len(_rows(temp_db, movie_cast)) == 2
    assert len(_rows(temp_db, movie_crew)) == 2


def test_person_in_cast_and_crew_is_one_person_row(temp_db):
    credits = {
        "cast": [{"id": 287, "name": "Brad Pitt", "character": "Tyler", "order": 1}],
        "crew": [
            {"id": 287, "name": "Brad Pitt", "department": "Production", "job": "Producer"}
        ],
    }
    load_credits(550, credits)
    assert len(_rows(temp_db, people)) == 1
    assert len(_rows(temp_db, movie_cast)) == 1
    assert len(_rows(temp_db, movie_crew)) == 1


def test_reingest_is_idempotent(temp_db):
    load_credits(550, CREDITS)
    load_credits(550, CREDITS)
    assert len(_rows(temp_db, people)) == 4
    assert len(_rows(temp_db, movie_cast)) == 2
    assert len(_rows(temp_db, movie_crew)) == 2


def test_duplicate_within_payload_collapsed(temp_db):
    credits = {
        "cast": [
            {"id": 287, "name": "Brad Pitt", "character": "Tyler", "order": 1},
            {"id": 287, "name": "Brad Pitt", "character": "Tyler", "order": 1},
        ],
        "crew": [
            {"id": 7467, "name": "Fincher", "department": "Directing", "job": "Director"},
            {"id": 7467, "name": "Fincher", "department": "Directing", "job": "Director"},
        ],
    }
    assert load_credits(550, credits) == {"cast": 1, "crew": 1}


def test_same_person_two_characters_makes_two_cast_rows(temp_db):
    credits = {
        "cast": [
            {"id": 287, "name": "Brad Pitt", "character": "Tyler", "order": 1},
            {"id": 287, "name": "Brad Pitt", "character": "The Narrator's projection", "order": 2},
        ],
        "crew": [],
    }
    counts = load_credits(550, credits)
    assert counts["cast"] == 2
    assert len(_rows(temp_db, people)) == 1
    assert len(_rows(temp_db, movie_cast)) == 2


def test_empty_and_missing_handled_safely(temp_db):
    assert load_credits(550, {}) == {"cast": 0, "crew": 0}
    assert load_credits(550, None) == {"cast": 0, "crew": 0}
    assert load_credits(550, {"cast": [{"name": "no id"}], "crew": []}) == {
        "cast": 0,
        "crew": 0,
    }
    assert len(_rows(temp_db, people)) == 0
