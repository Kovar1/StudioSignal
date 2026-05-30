"""Load a movie's keywords into keywords + movie_keywords."""
from sqlalchemy import delete, insert, select

from src.db import get_engine, keywords, movie_keywords


def _get_or_create_keyword(conn, tmdb_keyword_id, name):
    existing = conn.execute(
        select(keywords.c.id).where(keywords.c.tmdb_keyword_id == tmdb_keyword_id)
    ).first()
    if existing:
        return existing[0]
    result = conn.execute(
        insert(keywords).values(tmdb_keyword_id=tmdb_keyword_id, name=name)
    )
    return result.inserted_primary_key[0]


def load_keywords(movie_id, keywords_data):
    """Upsert keywords and (re)link them to ``movie_id``.

    ``keywords_data`` is the ``keywords`` slice from a movie detail payload:
    ``{"keywords": [{"id": ..., "name": ...}]}``. Links are cleared then
    re-inserted (idempotent). Returns the number of keywords linked.
    """
    keywords_data = keywords_data or {}
    items = keywords_data.get("keywords") or []

    deduped = {}
    for item in items:
        tmdb_keyword_id = item.get("id")
        if tmdb_keyword_id is None:
            continue
        deduped.setdefault(tmdb_keyword_id, item.get("name"))

    with get_engine().begin() as conn:
        conn.execute(
            delete(movie_keywords).where(movie_keywords.c.movie_id == movie_id)
        )
        for tmdb_keyword_id, name in deduped.items():
            keyword_id = _get_or_create_keyword(conn, tmdb_keyword_id, name)
            conn.execute(
                insert(movie_keywords).values(
                    movie_id=movie_id, keyword_id=keyword_id
                )
            )

    return len(deduped)
