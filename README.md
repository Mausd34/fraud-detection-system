# Fraud Detection System

Portfolio-grade transaction fraud-risk scoring service with a responsive browser dashboard and REST API.

## Features
- Transaction validation and risk scoring
- Low/medium/high risk classification
- Approve/review decision support
- Browser dashboard at `/`
- Swagger/OpenAPI at `/docs`
- Health endpoint
- Automated tests
- Docker-ready deployment

## Stack
Python · FastAPI · Pydantic · scikit-learn-ready architecture · Docker

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload
```
Open `http://127.0.0.1:8000/`.

## Docker
```bash
docker build -t fraud-detection-system .
docker run -p 8000:8000 fraud-detection-system
```

> Demo decision-support system. It is not a substitute for a regulated financial fraud-control process.
