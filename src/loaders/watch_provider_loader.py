"""Load a movie's watch providers into watch_providers + movie_watch_providers."""
from sqlalchemy import delete, insert, select

from src.db import get_engine, movie_watch_providers, watch_providers

# TMDb groups providers by how a title is offered. A "link" string also appears
# under each country block and is intentionally skipped by iterating only these.
ACCESS_TYPES = ("flatrate", "rent", "buy", "ads", "free")


def _get_or_create_provider(conn, tmdb_provider_id, provider_name):
    existing = conn.execute(
        select(watch_providers.c.id).where(
            watch_providers.c.tmdb_provider_id == tmdb_provider_id
        )
    ).first()
    if existing:
        return existing[0]
    result = conn.execute(
        insert(watch_providers).values(
            tmdb_provider_id=tmdb_provider_id, provider_name=provider_name
        )
    )
    return result.inserted_primary_key[0]


def load_watch_providers(movie_id, providers_data):
    """Upsert providers and (re)link them per country/access type for a movie.

    ``providers_data`` is the ``watch/providers`` slice:
    ``{"results": {"US": {"flatrate": [{provider}], "rent": [...]}, ...}}``.
    Links are cleared then re-inserted (idempotent); duplicate
    (provider, country, access) entries within the payload are collapsed.
    Returns the number of provider links created.
    """
    providers_data = providers_data or {}
    results = providers_data.get("results") or {}

    seen = set()
    rows = []
    for country_code, country_data in results.items():
        if not isinstance(country_data, dict):
            continue
        for access_type in ACCESS_TYPES:
            for provider in country_data.get(access_type) or []:
                tmdb_provider_id = provider.get("provider_id")
                if tmdb_provider_id is None:
                    continue
                key = (tmdb_provider_id, country_code, access_type)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    (
                        tmdb_provider_id,
                        provider.get("provider_name"),
                        country_code,
                        access_type,
                    )
                )

    with get_engine().begin() as conn:
        conn.execute(
            delete(movie_watch_providers).where(
                movie_watch_providers.c.movie_id == movie_id
            )
        )
        for tmdb_provider_id, provider_name, country_code, access_type in rows:
            provider_id = _get_or_create_provider(
                conn, tmdb_provider_id, provider_name
            )
            conn.execute(
                insert(movie_watch_providers).values(
                    movie_id=movie_id,
                    provider_id=provider_id,
                    country_code=country_code,
                    access_type=access_type,
                )
            )

    return len(rows)
