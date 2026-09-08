"""Demo authentication with SQLite persistence and signed bearer tokens."""
from datetime import datetime,timedelta,timezone
import hashlib,hmac,os,secrets,sqlite3
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
SECRET_KEY=os.getenv('JWT_SECRET','change-me-in-production'); DB=os.getenv('AUTH_DB','app.db')
router=APIRouter(prefix='/auth',tags=['auth'])
class Credentials(BaseModel): username:str=Field(min_length=3,max_length=80); password:str=Field(min_length=8,max_length=128)
def db():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT "user")'); c.commit(); return c
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def create_token(username,role='user',minutes=60):
 exp=int((datetime.now(timezone.utc)+timedelta(minutes=minutes)).timestamp()); nonce=secrets.token_hex(8); payload=f'{username}.{role}.{exp}.{nonce}'; sig=hmac.new(SECRET_KEY.encode(),payload.encode(),hashlib.sha256).hexdigest(); return f'{payload}.{sig}'
def verify_token(token):
 try:
  u,r,e,n,s=token.split('.'); p=f'{u}.{r}.{e}.{n}'; x=hmac.new(SECRET_KEY.encode(),p.encode(),hashlib.sha256).hexdigest(); return {'username':u,'role':r} if hmac.compare_digest(s,x) and int(e)>=int(datetime.now(timezone.utc).timestamp()) else None
 except Exception:return None
def current_user(authorization: str|None):
 if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Bearer token required')
 user=verify_token(authorization[7:]);
 if not user: raise HTTPException(401,'Invalid or expired token')
 return user
@router.post('/register')
def register(c:Credentials):
 con=db()
 try: con.execute('INSERT INTO users(username,password) VALUES (?,?)',(c.username,hash_password(c.password))); con.commit()
 except sqlite3.IntegrityError: raise HTTPException(409,'Username already exists')
 return {'message':'registered','username':c.username,'role':'user'}
 finally: con.close()
@router.post('/login')
def login(c:Credentials):
 con=db(); row=con.execute('SELECT username,password,role FROM users WHERE username=?',(c.username,)).fetchone(); con.close()
 if not row or not hmac.compare_digest(row[1],hash_password(c.password)): raise HTTPException(401,'Invalid credentials')
 return {'access_token':create_token(row[0],row[2]),'token_type':'bearer','user':{'username':row[0],'role':row[2]}}
@router.get('/me')
def me(authorization: str|None=Header(default=None)): return current_user(authorization)
