"""New endpoint tests: /api/websites and /api/dns/domains."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database.database import init_db  # noqa: E402
from app.main import app  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


class TestWebsites:
    def test_list_websites(self, client):
        resp = client.get("/api/websites")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        for row in resp.json():
            assert "website" in row
            assert "bytes" in row
            assert "count" in row

    def test_top_websites(self, client):
        resp = client.get("/api/websites/top?limit=3")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) <= 4  # 3 top + optional Other


class TestDns:
    def test_domains(self, client):
        resp = client.get("/api/dns/domains")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "domains" in body
        assert isinstance(body["domains"], list)


class TestLiveIncludesNewFields:
    def test_live_payload_has_websites(self, client):
        resp = client.get("/api/traffic/live")
        assert resp.status_code == 200
        body = resp.json()
        assert "websites" in body
        assert "active_connections" in body
        for conn in body["active_connections"]:
            assert "website" in conn
            assert "application" in conn

    def test_history_includes_website_application(self, client):
        resp = client.get("/api/traffic/history?limit=5")
        assert resp.status_code == 200
        for row in resp.json():
            assert "website" in row
            assert "domain" in row
            assert "application" in row