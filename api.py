from fastapi import FastAPI
from pydantic import BaseModel, Field
import math

app=FastAPI(title='Fraud Detection API',version='1.0.0')
class Transaction(BaseModel):
    amount: float=Field(gt=0)
    account_age_days: int=Field(ge=0)
    velocity_24h: int=Field(ge=0)
    distance_km: float=Field(ge=0)
    foreign: bool=False

def score(t: Transaction):
    risk=0
    if t.amount>=1000:risk+=30
    if t.amount>=5000:risk+=25
    if t.account_age_days<30:risk+=20
    if t.velocity_24h>=5:risk+=15
    if t.distance_km>=500:risk+=10
    if t.foreign:risk+=10
    risk=min(risk,100); label='high' if risk>=70 else 'medium' if risk>=40 else 'low'
    return risk,label

@app.get('/health')
def health(): return {'status':'ok','service':'fraud-detection-system'}
@app.post('/predict')
def predict(t: Transaction):
    risk,label=score(t)
    return {'risk_score':risk,'risk_level':label,'decision':'review' if risk>=40 else 'approve','model':'rule-based-demo-v1'}
