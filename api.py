from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest
import numpy as np

app=FastAPI(title='Fraud Detection System API',version='3.0.0',description='ML-assisted transaction anomaly scoring service')
class Transaction(BaseModel):
    amount:float=Field(gt=0); account_age_days:int=Field(ge=0); velocity_24h:int=Field(ge=0); distance_km:float=Field(ge=0); foreign:bool=False
rng=np.random.default_rng(42)
train=np.column_stack([rng.lognormal(4.2,0.6,1000),rng.integers(30,1500,1000),rng.integers(0,4,1000),rng.gamma(2,60,1000),rng.integers(0,2,1000)])
model=IsolationForest(contamination=0.04,random_state=42);model.fit(train)
def score(t:Transaction):
    x=np.array([[t.amount,t.account_age_days,t.velocity_24h,t.distance_km,int(t.foreign)]],dtype=float)
    raw=float(model.decision_function(x)[0]); anomaly=max(0,min(1,(0.15-raw)/0.30)); risk=round(anomaly*100,1); level='high' if risk>=70 else 'medium' if risk>=40 else 'low';return risk,level
@app.get('/health')
def health():return {'status':'ok','service':'fraud-detection-system','version':'3.0.0','engine':'isolation-forest'}
@app.post('/predict')
def predict(t:Transaction):
    risk,level=score(t);return {'risk_score':risk,'risk_level':level,'decision':'review' if risk>=40 else 'approve','model':'isolation-forest-demo-v1'}
app.mount('/',StaticFiles(directory='web',html=True),name='web')
