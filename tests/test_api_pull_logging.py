import types

import pytest
import requests
from sqlalchemy import select

from src.db import api_pull_logs
from src.ingestion import tmdb_client
from src.loaders.api_pull_log_loader import log_api_pull


def _all_logs(engine):
    with engine.connect() as conn:
        return conn.execute(select(api_pull_logs)).mappings().all()


def test_log_api_pull_inserts_success(temp_db):
    log_id = log_api_pull(
        endpoint="/movie/550",
        tmdb_id=550,
        request_params={"append_to_response": "external_ids"},
        status_code=200,
        success=True,
    )
    rows = _all_logs(temp_db)
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == log_id
    assert row["success"]
    assert row["tmdb_id"] == 550
    assert row["status_code"] == 200
    assert row["error_message"] is None
    # dict params are serialized to JSON text
    assert "append_to_response" in row["request_params"]


def test_log_api_pull_inserts_failure(temp_db):
    log_api_pull(
        endpoint="/movie/0",
        tmdb_id=0,
        status_code=404,
        success=False,
        error_message="404 Not Found",
    )
    rows = _all_logs(temp_db)
    assert len(rows) == 1
    row = rows[0]
    assert not row["success"]
    assert row["status_code"] == 404
    assert row["error_message"] == "404 Not Found"


def test_get_movie_details_logs_successful_pull(temp_db, monkeypatch):
    fake = types.SimpleNamespace(
        status_code=200,
        json=lambda: {"id": 550, "title": "Fight Club", "external_ids": {}},
    )
    monkeypatch.setattr(tmdb_client, "_request", lambda path, params=None: fake)

    data = tmdb_client.get_movie_details(550)
    assert data["id"] == 550

    rows = _all_logs(temp_db)
    assert len(rows) == 1
    assert rows[0]["success"]
    assert rows[0]["endpoint"] == "/movie/550"
    assert rows[0]["tmdb_id"] == 550
    assert rows[0]["status_code"] == 200


def test_get_movie_details_logs_failed_pull(temp_db, monkeypatch):
    response = types.SimpleNamespace(status_code=404)
    error = requests.HTTPError("404 Not Found", response=response)

    def boom(path, params=None):
        raise error

    monkeypatch.setattr(tmdb_client, "_request", boom)

    with pytest.raises(requests.HTTPError):
        tmdb_client.get_movie_details(99999999)

    rows = _all_logs(temp_db)
    assert len(rows) == 1
    assert not rows[0]["success"]
    assert rows[0]["tmdb_id"] == 99999999
    assert rows[0]["status_code"] == 404
    assert "404" in rows[0]["error_message"]
