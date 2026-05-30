"""Persist raw API payloads exactly as received."""
import json

from sqlalchemy import insert

from src.db import get_engine, raw_api_responses


def save_raw_response(source, endpoint, tmdb_id, response_json):
    """Insert a raw API response and return the new row id.

    ``response_json`` may be a dict (it will be serialized) or a JSON string.
    """
    if isinstance(response_json, str):
        payload = response_json
    else:
        payload = json.dumps(response_json)

    stmt = insert(raw_api_responses).values(
        source=source,
        endpoint=endpoint,
        tmdb_id=tmdb_id,
        response_json=payload,
    )

    with get_engine().begin() as conn:
        result = conn.execute(stmt)
        return result.inserted_primary_key[0]
