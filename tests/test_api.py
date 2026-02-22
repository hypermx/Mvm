"""Tests for the FastAPI backend."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.app import app, _adapters
from backend.db.orm_models import Base
from backend.db.session import get_db

_TEST_DATABASE_URL = "sqlite://"  # in-memory SQLite


@pytest.fixture()
def db_session():
    """Create a fresh in-memory SQLite database for each test.

    StaticPool ensures every connection shares the same in-memory database
    so that tables created by create_all are visible within the same test.
    """
    engine = create_engine(
        _TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """TestClient wired to the in-memory test database."""
    _adapters.clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    _adapters.clear()


@pytest.fixture()
def created_user(client) -> dict:
    payload = {
        "user_id": "api_test_user",
        "age": 30,
        "sex": "female",
        "migraine_history_years": 3.0,
        "average_migraine_frequency": 2.0,
    }
    resp = client.post("/users", json=payload)
    assert resp.status_code == 201
    return resp.json()


class TestUsers:
    def test_create_user(self, client):
        payload = {
            "user_id": "u1",
            "age": 28,
            "sex": "male",
            "migraine_history_years": 2.0,
            "average_migraine_frequency": 1.5,
        }
        resp = client.post("/users", json=payload)
        assert resp.status_code == 201
        assert resp.json()["user_id"] == "u1"

    def test_create_duplicate_user(self, client, created_user):
        payload = {
            "user_id": "api_test_user",
            "age": 30,
            "sex": "female",
            "migraine_history_years": 3.0,
            "average_migraine_frequency": 2.0,
        }
        resp = client.post("/users", json=payload)
        assert resp.status_code == 409

    def test_get_user(self, client, created_user):
        resp = client.get("/users/api_test_user")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "api_test_user"

    def test_get_nonexistent_user(self, client):
        resp = client.get("/users/nobody")
        assert resp.status_code == 404

    def test_update_user(self, client, created_user):
        update = {"age": 35, "sex": "male", "migraine_history_years": 10.0}
        resp = client.put("/users/api_test_user", json=update)
        assert resp.status_code == 200
        data = resp.json()
        assert data["age"] == 35
        assert data["sex"] == "male"
        assert data["migraine_history_years"] == 10.0
        # Unchanged fields retain original values
        assert data["average_migraine_frequency"] == 2.0

    def test_update_user_partial(self, client, created_user):
        resp = client.put("/users/api_test_user", json={"personal_threshold": 0.7})
        assert resp.status_code == 200
        assert resp.json()["personal_threshold"] == 0.7

    def test_update_nonexistent_user(self, client):
        resp = client.put("/users/nobody", json={"age": 25})
        assert resp.status_code == 404

    def test_update_user_invalid_sex(self, client, created_user):
        resp = client.put("/users/api_test_user", json={"sex": "unknown"})
        assert resp.status_code == 422


class TestLogs:
    def test_submit_log(self, client, created_user):
        log_payload = {
            "date": "2024-01-15",
            "sleep_hours": 7.5,
            "sleep_quality": 7.0,
            "stress_level": 3.0,
            "hydration_liters": 2.0,
            "caffeine_mg": 100.0,
            "alcohol_units": 0.0,
            "exercise_minutes": 30.0,
            "migraine_occurred": False,
        }
        resp = client.post("/logs/api_test_user", json=log_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "normalized_features" in data

    def test_submit_log_unknown_user(self, client):
        log_payload = {
            "date": "2024-01-15",
            "sleep_hours": 7.0,
            "sleep_quality": 6.0,
            "stress_level": 4.0,
            "hydration_liters": 2.0,
            "migraine_occurred": False,
        }
        resp = client.post("/logs/ghost_user", json=log_payload)
        assert resp.status_code == 404


class TestVulnerability:
    def test_get_vulnerability_no_logs(self, client, created_user):
        resp = client.get("/vulnerability/api_test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert "vulnerability_score" in data
        assert data["confidence"] == 0.0

    def test_get_vulnerability_with_logs(self, client, created_user):
        log_payload = {
            "date": "2024-01-15",
            "sleep_hours": 7.0,
            "sleep_quality": 6.0,
            "stress_level": 4.0,
            "hydration_liters": 2.0,
            "migraine_occurred": False,
        }
        client.post("/logs/api_test_user", json=log_payload)
        resp = client.get("/vulnerability/api_test_user")
        assert resp.status_code == 200
        score = resp.json()["vulnerability_score"]
        assert 0.0 <= score <= 1.0


class TestSimulation:
    def test_run_simulation(self, client, created_user):
        payload = {
            "user_id": "api_test_user",
            "baseline_logs": [
                {
                    "date": "2024-01-15",
                    "sleep_hours": 6.0,
                    "sleep_quality": 5.0,
                    "stress_level": 7.0,
                    "hydration_liters": 1.5,
                    "migraine_occurred": False,
                }
            ],
            "hypothetical_modifications": {"sleep_hours": 9.0},
        }
        resp = client.post("/simulate/api_test_user", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "trajectory" in data
        assert "migraine_risk" in data
        assert "uncertainty" in data


class TestInterventions:
    def test_get_interventions_no_logs(self, client, created_user):
        resp = client.get("/interventions/api_test_user")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
