import os
from pathlib import Path

from dotenv import load_dotenv


TEST_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(TEST_BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-not-for-production")
os.environ.setdefault("POSTGRES_PASSWORD", "test-only-password")

from .settings import *  # noqa: E402,F403
