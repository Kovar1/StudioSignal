"""End-to-end ingestion for a single movie.

Run from the project root as a module:

    python -m src.ingestion.run_one_movie
"""
from src.db import init_db
from src.ingestion.tmdb_client import get_movie_details
from src.loaders.enrichment import enrich_movie
from src.loaders.movie_loader import insert_weekly_snapshot, upsert_movie
from src.loaders.raw_loader import save_raw_response
from src.transforms.movie_transform import transform_movie_details

FIGHT_CLUB_ID = 550


def run(movie_id=FIGHT_CLUB_ID):
    """Pull one movie through the full pipeline and return the loaded row."""
    init_db()

    endpoint = f"/movie/{movie_id}"
    raw = get_movie_details(movie_id)
    raw_id = save_raw_response("tmdb", endpoint, movie_id, raw)

    movie = transform_movie_details(raw)
    upsert_movie(movie)
    enrich_movie(movie["movie_id"], raw)
    snapshot_id = insert_weekly_snapshot(movie)

    print(
        f"Success: ingested '{movie['title']}' (movie_id={movie['movie_id']}) "
        f"-> raw_api_responses id={raw_id}, "
        f"movies upserted, weekly snapshot id={snapshot_id}."
    )
    return movie


def main():
    run()


if __name__ == "__main__":
    main()
