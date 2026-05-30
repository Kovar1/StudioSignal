"""Load transformed movie rows and weekly snapshots into the database."""
from datetime import date

from sqlalchemy import insert, select, update

from src.db import get_engine, movie_weekly_snapshots, movies


def upsert_movie(movie_dict):
    """Insert a movie row, or update it in place if movie_id already exists."""
    movie_id = movie_dict["movie_id"]

    with get_engine().begin() as conn:
        exists = conn.execute(
            select(movies.c.movie_id).where(movies.c.movie_id == movie_id)
        ).first()

        if exists:
            conn.execute(
                update(movies)
                .where(movies.c.movie_id == movie_id)
                .values(**movie_dict)
            )
        else:
            conn.execute(insert(movies).values(**movie_dict))

    return movie_id


def insert_weekly_snapshot(movie_dict, snapshot_date=None):
    """Record today's point-in-time metrics for a movie and return the row id."""
    snapshot_date = snapshot_date or date.today()

    stmt = insert(movie_weekly_snapshots).values(
        snapshot_date=snapshot_date,
        movie_id=movie_dict["movie_id"],
        popularity=movie_dict.get("popularity"),
        vote_average=movie_dict.get("vote_average"),
        vote_count=movie_dict.get("vote_count"),
        revenue=movie_dict.get("revenue"),
        budget=movie_dict.get("budget"),
        status=movie_dict.get("status"),
        release_date=movie_dict.get("release_date"),
        runtime=movie_dict.get("runtime"),
        original_language=movie_dict.get("original_language"),
        imdb_id=movie_dict.get("imdb_id"),
    )

    with get_engine().begin() as conn:
        result = conn.execute(stmt)
        return result.inserted_primary_key[0]
