"""Configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///studiosignal.db")
