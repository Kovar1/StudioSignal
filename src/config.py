"""Configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Local default: a SQLite file in the project root. When DATABASE_URL is set
# (e.g. the Supabase Postgres URL provided via a GitHub Actions secret), the
# pipeline talks to that database instead -- no code change required. The URL
# may contain a password, so it is never logged or printed anywhere.
_DEFAULT_DATABASE_URL = "sqlite:///studiosignal.db"


def _resolve_database_url():
    """Pick the SQLite default unless DATABASE_URL points somewhere else."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return _DEFAULT_DATABASE_URL
    # Supabase/Heroku-style URLs sometimes use the legacy "postgres://" scheme,
    # which SQLAlchemy does not recognize -- it expects "postgresql://".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


DATABASE_URL = _resolve_database_url()
