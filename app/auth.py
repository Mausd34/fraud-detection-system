"""Small, dependency-free signed-token auth foundation for demo use."""
from datetime import datetime, timedelta, timezone
import hashlib, hmac, os, secrets
SECRET_KEY=os.getenv("JWT_SECRET","change-me-in-production")

def hash_password(password:str)->str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(username:str, minutes:int=60)->str:
    exp=int((datetime.now(timezone.utc)+timedelta(minutes=minutes)).timestamp()); nonce=secrets.token_hex(8)
    payload=f"{username}.{exp}.{nonce}"; sig=hmac.new(SECRET_KEY.encode(),payload.encode(),hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"

def verify_token(token:str):
    try:
        username,exp,nonce,sig=token.split('.'); payload=f"{username}.{exp}.{nonce}"
        expected=hmac.new(SECRET_KEY.encode(),payload.encode(),hashlib.sha256).hexdigest()
        return username if hmac.compare_digest(sig,expected) and int(exp)>=int(datetime.now(timezone.utc).timestamp()) else None
    except Exception:return None
