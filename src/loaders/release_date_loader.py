"""Load a movie's release dates into the release_dates table."""
from sqlalchemy import delete, insert

from src.db import get_engine, release_dates


def load_release_dates(movie_id, release_dates_data):
    """Replace ``movie_id``'s release_dates rows from the ``release_dates`` slice.

    ``release_dates_data`` is ``{"results": [{"iso_3166_1": "US",
    "release_dates": [{"certification", "release_date", "type", "note"}]}]}``.
    There is no natural unique key, so idempotency is achieved by deleting this
    movie's rows and re-inserting. Returns the number of rows inserted.
    """
    release_dates_data = release_dates_data or {}
    results = release_dates_data.get("results") or []

    inserted = 0
    with get_engine().begin() as conn:
        conn.execute(delete(release_dates).where(release_dates.c.movie_id == movie_id))
        for entry in results:
            country_code = entry.get("iso_3166_1")
            for rd in entry.get("release_dates") or []:
                conn.execute(
                    insert(release_dates).values(
                        movie_id=movie_id,
                        country_code=country_code,
                        certification=rd.get("certification") or None,
                        release_type=rd.get("type"),
                        release_date=rd.get("release_date") or None,
                        note=rd.get("note") or None,
                    )
                )
                inserted += 1

    return inserted
