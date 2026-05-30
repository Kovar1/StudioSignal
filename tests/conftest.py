import pytest
from sqlalchemy import create_engine

from src import db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the shared engine at a throwaway SQLite file with tables created.

    Loaders call db.get_engine() internally, so redirecting the cached engine
    keeps their writes off the real dev database during tests. monkeypatch
    restores the original engine after each test.
    """
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}", future=True)
    monkeypatch.setattr(db, "_engine", engine)
    db.init_db(engine)
    return engine
