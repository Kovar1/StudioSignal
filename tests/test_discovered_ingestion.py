from src.ingestion import run_discovered_ingestion as rdi
from src.ingestion.run_discovered_ingestion import (
    MovieIngestionResult,
    format_discovered_ingestion_summary,
    summarize_discovered_ingestion,
)


def _ok(movie_id, title="Some Movie"):
    return MovieIngestionResult(
        movie_id=movie_id,
        title=title,
        raw_saved=True,
        upserted=True,
        snapshot_created=True,
    )


def _fail(movie_id, error, *, raw_saved=False, upserted=False, snapshot_created=False):
    return MovieIngestionResult(
        movie_id=movie_id,
        raw_saved=raw_saved,
        upserted=upserted,
        snapshot_created=snapshot_created,
        error=error,
    )


def test_module_imports_cleanly():
    assert hasattr(rdi, "run_discovered_ingestion")
    assert hasattr(rdi, "ingest_movie")


def test_summary_all_succeeded():
    counts = summarize_discovered_ingestion([_ok(1), _ok(2), _ok(3)], discovered=3)
    assert counts == {
        "discovered": 3,
        "attempted": 3,
        "succeeded": 3,
        "failed": 0,
        "raw_saved": 3,
        "upserted": 3,
        "snapshots": 3,
    }


def test_summary_counts_failures_and_partial_steps():
    results = [
        _ok(1),
        _fail(2, "HTTPError: 404", raw_saved=True),  # got raw, failed before upsert
        _fail(3, "RuntimeError: no api key"),          # failed immediately
    ]
    counts = summarize_discovered_ingestion(results, discovered=3)
    assert counts["attempted"] == 3
    assert counts["succeeded"] == 1
    assert counts["failed"] == 2
    assert counts["raw_saved"] == 2
    assert counts["upserted"] == 1
    assert counts["snapshots"] == 1


def test_summary_discovered_defaults_to_attempted():
    counts = summarize_discovered_ingestion([_ok(1), _ok(2)])
    assert counts["discovered"] == 2
    assert counts["attempted"] == 2


def test_format_zero_failures():
    text = format_discovered_ingestion_summary([_ok(550, "Fight Club")], discovered=1)
    assert "Discovered ingestion complete." in text
    assert "Movies discovered: 1" in text
    assert "Movies succeeded: 1" in text
    assert "Movies failed: 0" in text
    assert "Weekly snapshots created: 1" in text
    assert "Failures:\nNone" in text


def test_format_mixed_success_and_failure():
    results = [_ok(550, "Fight Club"), _fail(12345, "API timeout")]
    text = format_discovered_ingestion_summary(results, discovered=2)
    assert "Movies discovered: 2" in text
    assert "Movies attempted: 2" in text
    assert "Movies succeeded: 1" in text
    assert "Movies failed: 1" in text
    assert "* movie_id=12345: API timeout" in text
