"""FastAPI application for a clearly labelled fraud-risk demo."""
import os
import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest

from app.auth import create_token, hash_password, verify_password, verify_token
from app.db import connect, init_db

app = FastAPI(
    title="Fraud Detection System API",
    version="4.1.0",
    description=(
        "Educational ML-assisted transaction anomaly scoring demo. "
        "Scores are not calibrated probabilities and must not be used as "
        "the sole basis for real financial decisions."
    ),
)
init_db()
security = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class Transaction(BaseModel):
    amount: float = Field(gt=0, le=1_000_000_000)
    account_age_days: int = Field(ge=0, le=100_000)
    velocity_24h: int = Field(ge=0, le=100_000)
    distance_km: float = Field(ge=0, le=50_000)
    foreign: bool = False


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    user = verify_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log in again.")
    return user


# Synthetic data is used only to make the demo reproducible; it is not a real
# fraud dataset and should not be interpreted as a validated production model.
_rng = np.random.default_rng(42)
_train = np.column_stack([
    _rng.lognormal(4.2, 0.6, 1000),
    _rng.integers(30, 1500, 1000),
    _rng.integers(0, 4, 1000),
    _rng.gamma(2, 60, 1000),
    _rng.integers(0, 2, 1000),
])
_model = IsolationForest(contamination=0.04, random_state=42)
_model.fit(_train)


def score_transaction(transaction: Transaction):
    row = np.array([[
        transaction.amount,
        transaction.account_age_days,
        transaction.velocity_24h,
        transaction.distance_km,
        int(transaction.foreign),
    ]], dtype=float)
    raw_score = float(_model.decision_function(row)[0])
    anomaly_score = max(0.0, min(1.0, (0.15 - raw_score) / 0.30))
    risk_score = round(anomaly_score * 100, 1)
    risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"
    return risk_score, risk_level


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "fraud-detection-system", "version": app.version,
            "engine": "isolation-forest-demo", "data": "synthetic"}


@app.post("/auth/register", tags=["authentication"], status_code=201)
def register(body: Credentials):
    with connect() as connection:
        existing = connection.execute(
            "SELECT 1 FROM users WHERE username = ?", (body.username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")
        connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (body.username, hash_password(body.password)),
        )
        connection.commit()
    return {"message": "registered", "username": body.username}


@app.post("/auth/login", tags=["authentication"])
def login(body: Credentials):
    with connect() as connection:
        user = connection.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?",
            (body.username,),
        ).fetchone()
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        # Upgrade older demo hashes after a successful login.
        if not user["password_hash"].startswith("pbkdf2_sha256$"):
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (hash_password(body.password), body.username),
            )
            connection.commit()
    return {
        "access_token": create_token(user["username"], user["role"]),
        "token_type": "bearer",
        "user": {"username": user["username"], "role": user["role"]},
    }


@app.get("/auth/me", tags=["authentication"])
def me(user=Depends(current_user)):
    return user


@app.post("/predict", tags=["prediction"])
def predict(transaction: Transaction, user=Depends(current_user)):
    risk_score, risk_level = score_transaction(transaction)
    return {
        "user": user["username"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": "review" if risk_score >= 40 else "approve",
        "model": "isolation-forest-demo-v1",
        "is_probability": False,
        "notice": "Demo score from synthetic training data; not a calibrated fraud probability.",
    }


app.mount("/", StaticFiles(directory="web", html=True), name="web")
