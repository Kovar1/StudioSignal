"""Flatten a raw TMDb movie payload into a row for the ``movies`` table."""
from datetime import datetime, timezone


def transform_movie_details(raw_json):
    """Return a flat dict of atomic values keyed by ``movies`` columns.

    Nested structures from TMDb (genres, production_companies, etc.) are
    intentionally dropped so every value is a scalar.
    """
    external_ids = raw_json.get("external_ids") or {}
    imdb_id = raw_json.get("imdb_id") or external_ids.get("imdb_id")

    return {
        "movie_id": raw_json.get("id"),
        "title": raw_json.get("title"),
        "original_title": raw_json.get("original_title"),
        # TMDb returns "" for unreleased titles; normalize to None.
        "release_date": raw_json.get("release_date") or None,
        "runtime": raw_json.get("runtime"),
        "budget": raw_json.get("budget"),
        "revenue": raw_json.get("revenue"),
        "original_language": raw_json.get("original_language"),
        "popularity": raw_json.get("popularity"),
        "vote_average": raw_json.get("vote_average"),
        "vote_count": raw_json.get("vote_count"),
        "status": raw_json.get("status"),
        "homepage": raw_json.get("homepage") or None,
        "imdb_id": imdb_id,
        "overview": raw_json.get("overview"),
        "updated_at": datetime.now(timezone.utc),
    }
