from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_live(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_ready_returns_503_when_db_is_down(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    r = client.get("/health/ready")
    assert r.status_code == 503


def test_response_has_request_id_header(client):
    r = client.get("/health/live")
    assert len(r.headers["X-Request-ID"]) >= 8
