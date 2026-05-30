from src.ingestion import discover_movies as dm
from src.ingestion.discover_movies import discover_movie_ids, format_discovery_summary

# Injectable fake sources with deliberate cross-source overlaps so dedupe and
# ordering are exercised without any network access.
FAKE_SOURCES = {
    "trending": lambda: [550, 27205, 155],
    "popular": lambda: [27205, 155, 680],
    "upcoming": lambda: [13, 550],
    "now_playing": lambda: [99, 100],
}
# combined order: 550,27205,155, 27205,155,680, 13,550, 99,100  -> 10 raw
# first-seen unique: 550,27205,155,680,13,99,100                 -> 7 unique


def test_module_imports_cleanly():
    assert hasattr(dm, "discover_movie_ids")
    assert hasattr(dm, "format_discovery_summary")


def test_source_counts_are_tracked():
    result = discover_movie_ids(limit=50, sources=FAKE_SOURCES)
    assert result.source_counts == {
        "trending": 3,
        "popular": 3,
        "upcoming": 2,
        "now_playing": 2,
    }
    assert result.total_raw_ids == 10


def test_dedupe_preserves_first_seen_order():
    result = discover_movie_ids(limit=50, sources=FAKE_SOURCES)
    assert result.ids == [550, 27205, 155, 680, 13, 99, 100]
    assert result.total_unique_ids == 7


def test_limit_is_applied():
    result = discover_movie_ids(limit=3, sources=FAKE_SOURCES)
    assert result.ids == [550, 27205, 155]
    assert len(result.ids) == 3
    # counts still reflect the full pre-limit picture
    assert result.total_raw_ids == 10
    assert result.total_unique_ids == 7
    assert result.limit == 3


def test_format_discovery_summary_contents():
    result = discover_movie_ids(limit=3, sources=FAKE_SOURCES)
    text = format_discovery_summary(result)

    assert "Discovery complete." in text
    for name in ("trending", "popular", "upcoming", "now_playing"):
        assert name in text
    assert "Total raw IDs: 10" in text
    assert "Unique movie IDs: 7" in text
    assert "Limited to: 3" in text
    assert "550, 27205, 155" in text
