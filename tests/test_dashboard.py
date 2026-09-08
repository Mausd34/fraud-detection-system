from fastapi.testclient import TestClient
from api import app
client=TestClient(app)
def test_health_contract():
    data=client.get('/health').json(); assert data['status']=='ok'
def test_low_risk_transaction():
    data=client.post('/predict',json={'amount':50,'account_age_days':365,'velocity_24h':1,'distance_km':2,'foreign':False}).json(); assert data['decision']=='approve'
