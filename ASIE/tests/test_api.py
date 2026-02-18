"""Tests for the REST API."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client; requires seed data to be present."""
    from asie.api.main import app
    return TestClient(app)


class TestAPIEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "ASIE" in r.json()["name"]

    def test_list_skills(self, client):
        r = client.get("/api/v1/skills")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200
        data = r.json()
        assert "skills" in data
        assert len(data["skills"]) > 0

    def test_trending(self, client):
        r = client.get("/api/v1/skills/trending")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200

    def test_emerging(self, client):
        r = client.get("/api/v1/skills/emerging")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200

    def test_at_risk(self, client):
        r = client.get("/api/v1/skills/at-risk")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200

    def test_alerts(self, client):
        r = client.get("/api/v1/alerts")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200

    def test_resume_analyze(self, client):
        r = client.post("/api/v1/resume/analyze", json={
            "resume_text": "Python developer with 5 years experience in machine learning and AWS."
        })
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200
        data = r.json()
        assert "extracted_skills" in data
        assert "skill_gaps" in data

    def test_skill_not_found(self, client):
        r = client.get("/api/v1/skills/nonexistent_skill_xyz/forecast")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 404

    def test_dashboard_summary(self, client):
        r = client.get("/api/v1/dashboard/summary")
        if r.status_code == 503:
            pytest.skip("Seed data not available")
        assert r.status_code == 200
        data = r.json()
        assert "total_skills_tracked" in data
