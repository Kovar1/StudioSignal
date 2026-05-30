"""Record every attempted TMDb API pull (success or failure)."""
import json

from sqlalchemy import insert

from src.db import api_pull_logs, get_engine


def log_api_pull(
    endpoint,
    tmdb_id=None,
    request_params=None,
    status_code=None,
    success=False,
    error_message=None,
):
    """Insert one api_pull_logs row and return its id.

    ``request_params`` may be a dict (serialized to JSON text) or a string.
    Callers should pass only logical params here, never the API key.
    """
    if request_params is not None and not isinstance(request_params, str):
        request_params = json.dumps(request_params)

    stmt = insert(api_pull_logs).values(
        endpoint=endpoint,
        tmdb_id=tmdb_id,
        request_params=request_params,
        status_code=status_code,
        success=success,
        error_message=error_message,
    )

    with get_engine().begin() as conn:
        result = conn.execute(stmt)
        return result.inserted_primary_key[0]
