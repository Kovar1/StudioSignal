"""Print discovered movie IDs. Read-only: no DB writes, no ingestion.

Run from the project root as a module:

    python -m src.ingestion.run_discovery
"""
from src.ingestion.discover_movies import discover_movie_ids, format_discovery_summary


def main():
    result = discover_movie_ids(limit=50)
    print(format_discovery_summary(result))


if __name__ == "__main__":
    main()
