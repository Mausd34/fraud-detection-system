"""Password hashing and signed demo bearer tokens."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

SECRET_KEY = os.getenv("JWT_SECRET", "local-development-only-change-me")
PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return "pbkdf2_sha256$" + str(PBKDF2_ITERATIONS) + "$" + salt + "$" + digest


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify new PBKDF2 hashes and legacy SHA-256 demo hashes."""
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected = stored_hash.split("$", 3)
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
            ).hex()
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def create_token(username: str, role: str = "user", minutes: int = 60) -> str:
    expiry = int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())
    nonce = secrets.token_hex(8)
    payload = f"{username}.{role}.{expiry}.{nonce}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_token(token: str):
    try:
        username, role, expiry, nonce, signature = token.split(".")
        payload = f"{username}.{role}.{expiry}.{nonce}"
        expected = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        valid_signature = hmac.compare_digest(signature, expected)
        not_expired = int(expiry) >= int(datetime.now(timezone.utc).timestamp())
        return {"username": username, "role": role} if valid_signature and not_expired else None
    except (ValueError, TypeError):
        return None
