from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app=FastAPI(title='Fraud Detection System API',version='2.0.0',description='Transaction fraud-risk scoring service')
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
    risk=min(risk,100)
    level='high' if risk>=70 else 'medium' if risk>=40 else 'low'
    return risk,level
@app.get('/health')
def health(): return {'status':'ok','service':'fraud-detection-system','version':'2.0.0'}
@app.post('/predict')
def predict(t:Transaction):
    risk,level=score(t)
    return {'risk_score':risk,'risk_level':level,'decision':'review' if risk>=40 else 'approve','model':'risk-engine-v2'}
app.mount('/',StaticFiles(directory='web',html=True),name='web')
