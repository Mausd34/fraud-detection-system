"""API smoke and authentication-flow tests."""
import secrets
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def credentials():
    return {
        "username": "test_" + secrets.token_hex(5),
        "password": "test-password-123",
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["data"] == "synthetic"


def test_prediction_requires_authentication():
    response = client.post(
        "/predict",
        json={
            "amount": 120,
            "account_age_days": 365,
            "velocity_24h": 1,
            "distance_km": 2,
            "foreign": False,
        },
    )
    assert response.status_code == 401


def test_register_login_and_predict():
    user = credentials()
    registered = client.post("/auth/register", json=user)
    assert registered.status_code == 201

    logged_in = client.post("/auth/login", json=user)
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    assert token

    profile = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["username"] == user["username"]

    prediction = client.post(
        "/predict",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "amount": 120,
            "account_age_days": 365,
            "velocity_24h": 1,
            "distance_km": 2,
            "foreign": False,
        },
    )
    assert prediction.status_code == 200
    result = prediction.json()
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"low", "medium", "high"}
    assert result["is_probability"] is False


def test_invalid_login_is_rejected():
    response = client.post("/auth/login", json=credentials())
    assert response.status_code == 401


def test_invalid_transaction_is_rejected_after_auth():
    user = credentials()
    client.post("/auth/register", json=user)
    token = client.post("/auth/login", json=user).json()["access_token"]
    response = client.post(
        "/predict",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": -1, "account_age_days": 1, "velocity_24h": 1, "distance_km": 1},
    )
    assert response.status_code == 422
