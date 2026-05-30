import pytest
from sqlalchemy import create_engine

from src import db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the shared engine at a throwaway SQLite file with tables created.

    Loaders call db.get_engine() internally, so redirecting the cached engine
    keeps their writes off the real dev database during tests. monkeypatch
    restores the original engine after each test.

    Autouse so EVERY test is isolated to a fresh SQLite database and can never
    reach a live Postgres/Supabase instance, even if DATABASE_URL happens to be
    set in the environment. Tests that assert on rows still request `temp_db`
    by name to receive this engine; the rest are protected automatically.
    """
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}", future=True)
    monkeypatch.setattr(db, "_engine", engine)
    db.init_db(engine)
    return engine
