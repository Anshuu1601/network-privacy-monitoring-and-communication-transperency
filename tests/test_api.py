"""API and report tests using FastAPI TestClient."""
import io
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


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "monitoring" in body


class TestInterfaces:
    def test_interfaces(self, client):
        resp = client.get("/api/interfaces")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestTraffic:
    def test_summary(self, client):
        resp = client.get("/api/traffic/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_connections" in body
        assert "bytes_sent" in body
        assert "bytes_received" in body

    def test_live(self, client):
        resp = client.get("/api/traffic/live")
        assert resp.status_code == 200
        body = resp.json()
        assert "summary" in body
        assert "privacy_score" in body

    def test_history(self, client):
        resp = client.get("/api/traffic/history?limit=10")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_over_time(self, client):
        resp = client.get("/api/traffic/over-time?bucket=30&hours=1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestDevices:
    def test_list_devices(self, client):
        resp = client.get("/api/devices")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_device_404(self, client):
        resp = client.get("/api/devices/99999")
        assert resp.status_code == 404


class TestPrivacy:
    def test_score(self, client):
        resp = client.get("/api/privacy/score")
        assert resp.status_code == 200
        body = resp.json()
        assert "score" in body
        assert 0 <= body["score"] <= 100

    def test_encryption(self, client):
        resp = client.get("/api/privacy/encryption")
        assert resp.status_code == 200
        body = resp.json()
        assert "encrypted_percentage" in body

    def test_summary(self, client):
        resp = client.get("/api/privacy/summary")
        assert resp.status_code == 200


class TestServices:
    def test_services(self, client):
        resp = client.get("/api/services")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_top(self, client):
        resp = client.get("/api/services/top")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAlerts:
    def test_alerts(self, client):
        resp = client.get("/api/alerts?limit=10")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_unencrypted(self, client):
        resp = client.get("/api/alerts/unencrypted")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestCapture:
    def test_status(self, client):
        resp = client.get("/api/capture/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "running" in body

    def test_start_demo(self, client):
        resp = client.post("/api/capture/start", json={"mode": "demo"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

    def test_stop(self, client):
        resp = client.post("/api/capture/stop")
        assert resp.status_code == 200


class TestReports:
    def test_daily_report(self, client):
        resp = client.get("/api/reports/daily")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_connections" in body
        assert "privacy_score" in body

    def test_weekly_report(self, client):
        resp = client.get("/api/reports/weekly")
        assert resp.status_code == 200
        assert resp.json()["report_type"] == "weekly"

    def test_custom_report(self, client):
        resp = client.get("/api/reports/custom?start=2026-01-01&end=2026-01-31")
        assert resp.status_code == 200
        assert resp.json()["report_type"] == "custom"

    def test_custom_missing_dates(self, client):
        resp = client.get("/api/reports/custom")
        assert resp.status_code == 422

    def test_csv_export(self, client):
        resp = client.get("/api/reports/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "timestamp" in resp.text

    def test_pdf_export(self, client):
        resp = client.get("/api/reports/export/pdf?report_type=daily")
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers["content-type"]
        assert resp.content.startswith(b"%PDF")


class TestValidation:
    def test_invalid_device_id(self, client):
        resp = client.get("/api/devices/abc")
        assert resp.status_code == 422

    def test_invalid_limit(self, client):
        resp = client.get("/api/traffic/history?limit=-5")
        assert resp.status_code == 422