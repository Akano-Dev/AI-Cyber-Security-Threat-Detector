"""Test fixtures. Env vars are set BEFORE importing the app so settings pick them up."""
import os
import tempfile

# Isolate the test DB and pin a known API key (env overrides .env in pydantic-settings).
_TEST_DB = os.path.join(tempfile.gettempdir(), "acstd_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["DB_PATH"] = _TEST_DB
os.environ["API_KEY"] = "test-key"

import pytest
from fastapi.testclient import TestClient

from app.main import app

API_KEY = "test-key"


@pytest.fixture(scope="session")
def client():
    # `with TestClient` runs the lifespan (init_db, load model).
    with TestClient(app) as c:
        yield c
