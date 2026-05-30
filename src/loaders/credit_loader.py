"""Load a movie's cast and crew into people + movie_cast + movie_crew."""
from sqlalchemy import delete, insert, select

from src.db import get_engine, movie_cast, movie_crew, people


def _get_or_create_person(conn, tmdb_person_id, name):
    existing = conn.execute(
        select(people.c.id).where(people.c.tmdb_person_id == tmdb_person_id)
    ).first()
    if existing:
        return existing[0]
    result = conn.execute(
        insert(people).values(tmdb_person_id=tmdb_person_id, name=name)
    )
    return result.inserted_primary_key[0]


def load_credits(movie_id, credits_data):
    """Upsert people and (re)link cast + crew for ``movie_id``.

    ``credits_data`` is the ``credits`` slice: ``{"cast": [...], "crew": [...]}``.
    Cast/crew links for this movie are cleared then re-inserted (idempotent).
    Duplicate (person, character) or (person, department, job) entries within the
    payload are collapsed. Returns ``{"cast": n, "crew": m}`` link counts.
    """
    credits_data = credits_data or {}
    cast_items = credits_data.get("cast") or []
    crew_items = credits_data.get("crew") or []

    seen_cast = set()
    seen_crew = set()

    with get_engine().begin() as conn:
        conn.execute(delete(movie_cast).where(movie_cast.c.movie_id == movie_id))
        conn.execute(delete(movie_crew).where(movie_crew.c.movie_id == movie_id))

        for item in cast_items:
            tmdb_person_id = item.get("id")
            if tmdb_person_id is None:
                continue
            character = item.get("character") or ""
            key = (tmdb_person_id, character)
            if key in seen_cast:
                continue
            seen_cast.add(key)
            person_id = _get_or_create_person(conn, tmdb_person_id, item.get("name"))
            conn.execute(
                insert(movie_cast).values(
                    movie_id=movie_id,
                    person_id=person_id,
                    character=character,
                    cast_order=item.get("order"),
                )
            )

        for item in crew_items:
            tmdb_person_id = item.get("id")
            if tmdb_person_id is None:
                continue
            department = item.get("department") or ""
            job = item.get("job") or ""
            key = (tmdb_person_id, department, job)
            if key in seen_crew:
                continue
            seen_crew.add(key)
            person_id = _get_or_create_person(conn, tmdb_person_id, item.get("name"))
            conn.execute(
                insert(movie_crew).values(
                    movie_id=movie_id,
                    person_id=person_id,
                    department=department,
                    job=job,
                )
            )

    return {"cast": len(seen_cast), "crew": len(seen_crew)}
