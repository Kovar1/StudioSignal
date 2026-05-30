from sqlalchemy import create_engine, inspect

from src.db import init_db


def test_tables_can_be_created(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")

    init_db(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {
        "raw_api_responses",
        "movies",
        "movie_weekly_snapshots",
        "api_pull_logs",
        "genres",
        "movie_genres",
        "people",
        "movie_cast",
        "movie_crew",
        "keywords",
        "movie_keywords",
        "watch_providers",
        "movie_watch_providers",
        "release_dates",
    } <= table_names
