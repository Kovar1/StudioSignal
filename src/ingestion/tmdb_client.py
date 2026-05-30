"""Thin client for the TMDb REST API."""
import requests

from src.config import TMDB_API_KEY
from src.loaders.api_pull_log_loader import log_api_pull

BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_TIMEOUT = 30


def _request(path, params=None):
    """Low-level GET returning the raw Response (after raise_for_status).

    Centralizes API key injection. Raises RuntimeError if the API key is
    missing and requests.HTTPError on a non-2xx response.
    """
    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    query = {"api_key": TMDB_API_KEY}
    if params:
        query.update(params)

    response = requests.get(f"{BASE_URL}{path}", params=query, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response


def get_json(path, params=None):
    """GET a TMDb API path and return the parsed JSON body."""
    return _request(path, params).json()


def get_movie_details(movie_id):
    """Fetch full movie details (plus external IDs), logging the pull attempt."""
    endpoint = f"/movie/{movie_id}"
    params = {
        "append_to_response": "credits,keywords,watch/providers,release_dates,external_ids"
    }

    try:
        response = _request(endpoint, params)
    except Exception as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        log_api_pull(
            endpoint=endpoint,
            tmdb_id=movie_id,
            request_params=params,
            status_code=status_code,
            success=False,
            error_message=f"{type(exc).__name__}: {exc}",
        )
        raise

    log_api_pull(
        endpoint=endpoint,
        tmdb_id=movie_id,
        request_params=params,
        status_code=response.status_code,
        success=True,
        error_message=None,
    )
    return response.json()
