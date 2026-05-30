from src.loaders import enrichment

RAW = {
    "genres": [{"id": 18, "name": "Drama"}],
    "credits": {
        "cast": [{"id": 1, "name": "A", "character": "X", "order": 0}],
        "crew": [],
    },
    "keywords": {"keywords": [{"id": 5, "name": "k"}]},
    "watch/providers": {"results": {}},
    "release_dates": {"results": []},
}


def test_enrich_movie_loads_every_category(temp_db):
    outcomes = enrichment.enrich_movie(550, RAW)
    assert set(outcomes) == {
        "genres",
        "credits",
        "keywords",
        "watch_providers",
        "release_dates",
    }
    assert all(o["ok"] for o in outcomes.values())
    assert outcomes["genres"]["result"] == 1
    assert outcomes["credits"]["result"] == {"cast": 1, "crew": 0}
    assert outcomes["keywords"]["result"] == 1


def test_one_category_failure_is_isolated(temp_db, monkeypatch):
    def boom(movie_id, data):
        raise ValueError("genre kaboom")

    monkeypatch.setattr(enrichment, "load_genres", boom)

    outcomes = enrichment.enrich_movie(550, RAW)

    assert outcomes["genres"]["ok"] is False
    assert "genre kaboom" in outcomes["genres"]["error"]
    # The remaining categories still load successfully.
    assert outcomes["credits"]["ok"] is True
    assert outcomes["credits"]["result"] == {"cast": 1, "crew": 0}
    assert outcomes["keywords"]["ok"] is True


def test_missing_slices_are_safe(temp_db):
    outcomes = enrichment.enrich_movie(550, {})
    assert all(o["ok"] for o in outcomes.values())
    assert outcomes["genres"]["result"] == 0
    assert outcomes["credits"]["result"] == {"cast": 0, "crew": 0}
    assert outcomes["release_dates"]["result"] == 0


def test_none_payload_is_safe(temp_db):
    outcomes = enrichment.enrich_movie(550, None)
    assert all(o["ok"] for o in outcomes.values())
