"""Quick connectivity check for the active StudioSignal database.

Talks to SQLite locally by default, or to the DATABASE_URL database (e.g. the
Supabase Postgres instance) when that environment variable is set. It creates
the schema if needed, reports whether it reached SQLite or Postgres, confirms
the connection is live, and prints a per-table row count.

It never prints the password or the full connection string -- only the backend
kind (derived from the SQLAlchemy dialect) and table counts.

Run from the project root as a module:

    python -m src.ingestion.check_db_connection
"""
from sqlalchemy import func, select

from src.db import database_kind, init_db, metadata


def check_connection():
    """Create the schema, confirm the connection, and print a safe summary."""
    engine = init_db()
    kind = database_kind(engine)
    print(f"Database type: {kind}")

    with engine.connect() as conn:
        print("Connection: OK")
        print("Tables:")
        for table in metadata.sorted_tables:
            count = conn.execute(select(func.count()).select_from(table)).scalar()
            print(f"  {table.name}: {count}")

    return kind


def main():
    check_connection()


if __name__ == "__main__":
    main()
