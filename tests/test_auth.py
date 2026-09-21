from tests.conftest import PASSWORD


def _register(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def test_register_success_does_not_leak_password(client):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_email_conflicts(client):
    assert _register(client).status_code == 201
    assert _register(client, email="ALICE@example.com").status_code == 409


def test_register_weak_password_rejected(client):
    assert _register(client, password="short").status_code == 422


def test_register_invalid_email_rejected(client):
    assert _register(client, email="not-an-email").status_code == 422


def test_login_success_returns_bearer_token(client):
    _register(client)
    r = client.post(
        "/api/v1/auth/login", data={"username": "alice@example.com", "password": PASSWORD}
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    _register(client)
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "alice@example.com", "password": "wrong-password-123"},
    )
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post(
        "/api/v1/auth/login", data={"username": "ghost@example.com", "password": PASSWORD}
    )
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/v1/tasks").status_code == 401


def test_protected_route_rejects_garbage_token(client):
    r = client.get("/api/v1/tasks", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401
