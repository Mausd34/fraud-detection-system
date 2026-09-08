from fastapi import FastAPI,HTTPException,Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from pydantic import BaseModel,Field
from sklearn.ensemble import IsolationForest
import numpy as np
from app.auth import hash_password,create_token,verify_token
from app.db import connect,init_db
app=FastAPI(title='Fraud Detection System API',version='4.0.0',description='ML-assisted transaction anomaly scoring service')
init_db();security=HTTPBearer(auto_error=False)
class Credentials(BaseModel): username:str=Field(min_length=3,max_length=80);password:str=Field(min_length=6,max_length=200)
class Transaction(BaseModel): amount:float=Field(gt=0);account_age_days:int=Field(ge=0);velocity_24h:int=Field(ge=0);distance_km:float=Field(ge=0);foreign:bool=False
def current_user(c:HTTPAuthorizationCredentials=Depends(security)):
    if not c:raise HTTPException(401,'Authentication required')
    u=verify_token(c.credentials)
    if not u:raise HTTPException(401,'Invalid or expired token')
    return u
rng=np.random.default_rng(42);train=np.column_stack([rng.lognormal(4.2,0.6,1000),rng.integers(30,1500,1000),rng.integers(0,4,1000),rng.gamma(2,60,1000),rng.integers(0,2,1000)])
model=IsolationForest(contamination=0.04,random_state=42);model.fit(train)
def score(t):
    x=np.array([[t.amount,t.account_age_days,t.velocity_24h,t.distance_km,int(t.foreign)]],dtype=float);raw=float(model.decision_function(x)[0]);anomaly=max(0,min(1,(0.15-raw)/0.30));risk=round(anomaly*100,1);level='high' if risk>=70 else 'medium' if risk>=40 else 'low';return risk,level
@app.get('/health')
def health():return {'status':'ok','service':'fraud-detection-system','version':'4.0.0','engine':'isolation-forest'}
@app.post('/auth/register')
def register(b:Credentials):
    with connect() as c:
        if c.execute('SELECT 1 FROM users WHERE username=?',(b.username,)).fetchone():raise HTTPException(409,'Username already exists')
        c.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(b.username,hash_password(b.password)));c.commit()
    return {'message':'registered','username':b.username}
@app.post('/auth/login')
def login(b:Credentials):
    with connect() as c:u=c.execute('SELECT * FROM users WHERE username=?',(b.username,)).fetchone()
    if not u or u['password_hash']!=hash_password(b.password):raise HTTPException(401,'Invalid username or password')
    return {'access_token':create_token(u['username']),'token_type':'bearer'}
@app.get('/auth/me')
def me(u=Depends(current_user)):return u
@app.post('/predict')
def predict(t:Transaction,u=Depends(current_user)):
    risk,level=score(t);return {'user':u['username'],'risk_score':risk,'risk_level':level,'decision':'review' if risk>=40 else 'approve','model':'isolation-forest-demo-v1'}
app.mount('/',StaticFiles(directory='web',html=True),name='web')
