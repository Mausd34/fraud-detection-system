from fastapi.testclient import TestClient
from api import app
client=TestClient(app)
def test_health():
    r=client.get('/health'); assert r.status_code==200

def test_prediction():
    r=client.post('/predict',json={'amount':120,'account_age_days':365,'velocity_24h':1,'distance_km':2,'foreign':False})
    assert r.status_code==200
    assert 'risk_score' in r.json()
