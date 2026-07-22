"""Authentication, refresh rotation, and the per-token request limit."""

import pytest


@pytest.mark.parametrize(
    "username, password",
    [
        ("demo", "password123"),
        ("admin", "admin123"),
    ],
)
def test_login_success(client, username, password):
    # Every seeded user must authenticate against the users table.
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.parametrize(
    "username, password",
    [
        ("demo", "nope"),  # correct user, wrong password
        ("ghost", "password123"),  # unknown user
    ],
)
def test_login_rejects_bad_credentials(client, username, password):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/products")
    assert resp.status_code in (401, 403)


def test_refresh_returns_new_pair_and_rotates(client, tokens):
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_pair = resp.json()
    assert new_pair["access_token"] != tokens["access_token"]

    # The old refresh token has been rotated out and can no longer be used.
    reused = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reused.status_code == 401


def test_refresh_rejects_invalid_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


def test_refresh_rejects_access_token(client, tokens):
    # An access token must not be accepted where a refresh token is expected.
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_access_token_request_limit(client, tokens, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_requests_per_token", 3)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    for _ in range(3):
        assert client.get("/products", headers=headers).status_code == 200

    # The 4th authenticated request exceeds the limit.
    assert client.get("/products", headers=headers).status_code == 401


def test_refreshed_token_works_after_limit(client, tokens, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_requests_per_token", 2)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    for _ in range(2):
        assert client.get("/products", headers=headers).status_code == 200
    assert client.get("/products", headers=headers).status_code == 401

    new_pair = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).json()
    new_headers = {"Authorization": f"Bearer {new_pair['access_token']}"}
    assert client.get("/products", headers=new_headers).status_code == 200


def test_response_exposes_token_usage_headers(auth_client):
    resp = auth_client.get("/products")
    assert resp.status_code == 200
    assert resp.headers["X-Token-Requests-Used"] == "1"
    assert resp.headers["X-Token-Requests-Limit"] == "20"
    assert resp.headers["X-Token-Expires-At"]


def test_access_token_expires_after_ttl(client, monkeypatch):
    from app.config import settings

    # Issue a token that is already past its TTL, then use it.
    monkeypatch.setattr(settings, "access_token_ttl_seconds", -1)
    tokens = client.post(
        "/auth/login", json={"username": "demo", "password": "password123"}
    ).json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/products", headers=headers).status_code == 401


@pytest.mark.parametrize(
    "make_token",
    [
        pytest.param(lambda tokens: "not-a-real-jwt", id="malformed"),
        pytest.param(lambda tokens: tokens["refresh_token"], id="refresh-as-access"),
    ],
)
def test_invalid_bearer_token_rejected(client, tokens, make_token):
    # Neither a garbage token nor a refresh token may be used as an access token.
    headers = {"Authorization": f"Bearer {make_token(tokens)}"}
    assert client.get("/products", headers=headers).status_code == 401
