"""Database engine, schema definition, and table creation."""
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
)

from src.config import DATABASE_URL

metadata = MetaData()

raw_api_responses = Table(
    "raw_api_responses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False),
    Column("endpoint", String, nullable=False),
    Column("tmdb_id", Integer),
    Column("response_json", Text, nullable=False),
    Column("pulled_at", DateTime, server_default=func.now(), nullable=False),
)

movies = Table(
    "movies",
    metadata,
    Column("movie_id", Integer, primary_key=True, autoincrement=False),
    Column("title", String),
    Column("original_title", String),
    Column("release_date", String),
    Column("runtime", Integer),
    Column("budget", BigInteger),
    Column("revenue", BigInteger),
    Column("original_language", String),
    Column("popularity", Float),
    Column("vote_average", Float),
    Column("vote_count", Integer),
    Column("status", String),
    Column("homepage", String),
    Column("imdb_id", String),
    Column("overview", Text),
    Column("updated_at", DateTime),
)

movie_weekly_snapshots = Table(
    "movie_weekly_snapshots",
    metadata,
    Column("snapshot_id", Integer, primary_key=True, autoincrement=True),
    Column("snapshot_date", Date, nullable=False),
    Column("movie_id", Integer, nullable=False),
    Column("popularity", Float),
    Column("vote_average", Float),
    Column("vote_count", Integer),
    Column("revenue", BigInteger),
    Column("budget", BigInteger),
    Column("status", String),
    Column("release_date", String),
    Column("runtime", Integer),
    Column("original_language", String),
    Column("imdb_id", String),
)

api_pull_logs = Table(
    "api_pull_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("endpoint", String, nullable=False),
    Column("tmdb_id", Integer),
    Column("request_params", Text),
    Column("status_code", Integer),
    Column("success", Boolean, nullable=False),
    Column("error_message", Text),
    Column("pulled_at", DateTime, server_default=func.now(), nullable=False),
)

# --- Enrichment dimension + link tables --------------------------------------
# Dimension tables (genres, people, keywords, watch_providers) carry a surrogate
# id and a unique tmdb_* id; loaders get-or-create them. Link tables use a
# composite primary key over their natural key, which both enforces "no
# duplicate rows" and matches the columns the schema spec lists.

genres = Table(
    "genres",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tmdb_genre_id", Integer, unique=True, nullable=False),
    Column("name", String),
)

movie_genres = Table(
    "movie_genres",
    metadata,
    Column("movie_id", Integer, primary_key=True),
    Column("genre_id", Integer, primary_key=True),
)

people = Table(
    "people",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tmdb_person_id", Integer, unique=True, nullable=False),
    Column("name", String),
)

movie_cast = Table(
    "movie_cast",
    metadata,
    Column("movie_id", Integer, primary_key=True),
    Column("person_id", Integer, primary_key=True),
    Column("character", String, primary_key=True),
    Column("cast_order", Integer),
)

movie_crew = Table(
    "movie_crew",
    metadata,
    Column("movie_id", Integer, primary_key=True),
    Column("person_id", Integer, primary_key=True),
    Column("department", String, primary_key=True),
    Column("job", String, primary_key=True),
)

keywords = Table(
    "keywords",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tmdb_keyword_id", Integer, unique=True, nullable=False),
    Column("name", String),
)

movie_keywords = Table(
    "movie_keywords",
    metadata,
    Column("movie_id", Integer, primary_key=True),
    Column("keyword_id", Integer, primary_key=True),
)

watch_providers = Table(
    "watch_providers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tmdb_provider_id", Integer, unique=True, nullable=False),
    Column("provider_name", String),
)

movie_watch_providers = Table(
    "movie_watch_providers",
    metadata,
    Column("movie_id", Integer, primary_key=True),
    Column("provider_id", Integer, primary_key=True),
    Column("country_code", String, primary_key=True),
    Column("access_type", String, primary_key=True),
)

release_dates = Table(
    "release_dates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("movie_id", Integer, nullable=False),
    Column("country_code", String),
    Column("certification", String),
    Column("release_type", Integer),
    Column("release_date", String),
    Column("note", String),
)

_engine = None


def get_engine():
    """Return a process-wide SQLAlchemy engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, future=True)
    return _engine


def init_db(engine=None):
    """Create all tables if they do not already exist."""
    engine = engine or get_engine()
    metadata.create_all(engine)
    return engine


def get_connection():
    """Open a new connection on the shared engine."""
    return get_engine().connect()
