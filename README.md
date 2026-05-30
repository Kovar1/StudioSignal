# StudioSignal

A modular Python data ingestion pipeline for movie data. StudioSignal pulls
movie details from the [TMDb API](https://developer.themoviedb.org/), stores the
raw JSON response, transforms it into clean atomic fields, and loads it into a
relational database.

This is the first MVP milestone: a **single movie** moving through the full
pipeline — API call → raw JSON storage → transform → `movies` table → weekly
snapshot.

## Architecture

```
src/
├── config.py                  # loads TMDB_API_KEY and DATABASE_URL from env
├── db.py                      # SQLAlchemy engine + table definitions / creation
├── ingestion/
│   ├── tmdb_client.py         # get_movie_details(movie_id)
│   └── run_one_movie.py       # orchestrates the full pipeline for one movie
├── transforms/
│   └── movie_transform.py     # transform_movie_details(raw_json)
└── loaders/
    ├── raw_loader.py          # save_raw_response(...)
    └── movie_loader.py        # upsert_movie(...) / insert_weekly_snapshot(...)
```

### Tables

- **raw_api_responses** — every raw payload, stored verbatim for replay/audit.
- **movies** — one flat, current row per movie (`movie_id` is the primary key).
- **movie_weekly_snapshots** — point-in-time metrics, one row per run.

## Setup

Requires Python 3.10+.

```bash
# 1. (recommended) create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. configure environment variables
cp .env.example .env          # Windows: copy .env.example .env
# then edit .env and set TMDB_API_KEY to your TMDb API key
```

`DATABASE_URL` defaults to a local SQLite file (`sqlite:///studiosignal.db`).
You can point it at any SQLAlchemy-supported database by editing `.env`.

## Run one movie

Pulls movie ID 550 (*Fight Club*) through the entire pipeline:

```bash
python -m src.ingestion.run_one_movie
```

On success it prints a confirmation line and the local SQLite database
(`studiosignal.db`) will contain one raw response, one movie row, and one
weekly snapshot.

> Run as a module (`-m`) from the project root so the `src` package imports
> resolve correctly.

## Run tests

```bash
pytest
```

The test suite covers the transform logic, table creation, and that the
ingestion entrypoint imports cleanly — none of these tests require a network
connection or a real API key.
