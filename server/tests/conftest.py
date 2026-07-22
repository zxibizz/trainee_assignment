"""Shared test fixtures for the server test suite.

Environment defaults are set before the app is imported so the app uses an
isolated database, no artificial delay, and a fresh in-memory auth state.
"""

import os
import tempfile

# Configure the app before it is imported anywhere.
_tmp_db = os.path.join(tempfile.gettempdir(), "products_test.db")
os.environ.setdefault("DATABASE_PATH", _tmp_db)
os.environ.setdefault("DOWNSTREAM_EVENT_BUS_LATENCY_SECONDS", "0")
os.environ.setdefault("MAX_REQUESTS_PER_TOKEN", "20")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """A TestClient whose lifespan re-seeds the database for each test."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def tokens(client):
    """Log in as the demo user and return the issued token pair."""
    resp = client.post(
        "/auth/login", json={"username": "demo", "password": "password123"}
    )
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture()
def auth_client(client, tokens):
    """A TestClient with a valid access token applied to every request."""
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    return client


@pytest.fixture()
def admin_tokens(client):
    """Log in as the demo admin and return the issued token pair."""
    resp = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture()
def admin_client(client, admin_tokens):
    """A TestClient authenticated as the admin user."""
    client.headers.update({"Authorization": f"Bearer {admin_tokens['access_token']}"})
    return client
