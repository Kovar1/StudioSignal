from src.ingestion import run_smoke_test as smoke
from src.ingestion.run_smoke_test import (
    MOVIE_IDS,
    MovieResult,
    format_summary,
    summarize,
)


def test_module_imports_cleanly():
    assert hasattr(smoke, "run_smoke_test")


def test_movie_id_list_has_five_ids():
    assert len(MOVIE_IDS) == 5
    assert all(isinstance(movie_id, int) for movie_id in MOVIE_IDS)


def test_summarize_all_succeeded():
    results = [
        MovieResult(movie_id=mid, raw_saved=True, upserted=True, snapshot_created=True)
        for mid in (1, 2, 3)
    ]
    counts = summarize(results)
    assert counts == {
        "attempted": 3,
        "succeeded": 3,
        "failed": 0,
        "raw_saved": 3,
        "upserted": 3,
        "snapshots": 3,
    }


def test_summarize_counts_failures_and_partial_steps():
    results = [
        MovieResult(movie_id=1, raw_saved=True, upserted=True, snapshot_created=True),
        # got as far as saving raw, then blew up before upserting
        MovieResult(movie_id=2, raw_saved=True, error="HTTPError: 404"),
        # failed immediately
        MovieResult(movie_id=3, error="RuntimeError: no api key"),
    ]
    counts = summarize(results)
    assert counts["attempted"] == 3
    assert counts["succeeded"] == 1
    assert counts["failed"] == 2
    assert counts["raw_saved"] == 2
    assert counts["upserted"] == 1
    assert counts["snapshots"] == 1


def test_format_summary_reports_no_failures():
    results = [
        MovieResult(movie_id=550, raw_saved=True, upserted=True, snapshot_created=True)
    ]
    text = format_summary(results)
    assert "Smoke test complete." in text
    assert "Movies succeeded: 1" in text
    assert "Movies failed: 0" in text
    assert "Failures:\nNone" in text


def test_format_summary_lists_each_failure():
    results = [
        MovieResult(movie_id=550, raw_saved=True, upserted=True, snapshot_created=True),
        MovieResult(movie_id=99999999, error="HTTPError: 404 Not Found"),
    ]
    text = format_summary(results)
    assert "Movies attempted: 2" in text
    assert "Movies failed: 1" in text
    assert "* movie_id=99999999: HTTPError: 404 Not Found" in text
