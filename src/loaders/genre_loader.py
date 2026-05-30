"""Load a movie's genres into the genres + movie_genres tables."""
from sqlalchemy import delete, insert, select

from src.db import genres, get_engine, movie_genres


def _get_or_create_genre(conn, tmdb_genre_id, name):
    existing = conn.execute(
        select(genres.c.id).where(genres.c.tmdb_genre_id == tmdb_genre_id)
    ).first()
    if existing:
        return existing[0]
    result = conn.execute(insert(genres).values(tmdb_genre_id=tmdb_genre_id, name=name))
    return result.inserted_primary_key[0]


def load_genres(movie_id, genres_data):
    """Upsert genres and (re)link them to ``movie_id``.

    ``genres_data`` is the ``genres`` list from a movie detail payload, e.g.
    ``[{"id": 18, "name": "Drama"}, ...]``. Existing movie_genres rows for this
    movie are cleared first, then re-inserted, so a re-ingest never duplicates
    links. Returns the number of genres linked.
    """
    deduped = {}
    for item in genres_data or []:
        tmdb_genre_id = item.get("id")
        if tmdb_genre_id is None:
            continue
        deduped.setdefault(tmdb_genre_id, item.get("name"))

    with get_engine().begin() as conn:
        conn.execute(delete(movie_genres).where(movie_genres.c.movie_id == movie_id))
        for tmdb_genre_id, name in deduped.items():
            genre_id = _get_or_create_genre(conn, tmdb_genre_id, name)
            conn.execute(
                insert(movie_genres).values(movie_id=movie_id, genre_id=genre_id)
            )

    return len(deduped)
