import jwt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- PASSWORD ----------------
def hash_password(password):
    password = str(password).strip()

    # ✅ PRE-HASH (fixes 72 byte limit)
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    return pwd_context.hash(pre_hashed)


def verify_password(password, hashed):
    password = str(password).strip()

    # ✅ SAME PRE-HASH
    pre_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    return pwd_context.verify(pre_hashed, hashed)


# ---------------- ACCESS TOKEN ----------------
def create_access_token(data):
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=15)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------- REFRESH TOKEN ----------------
def create_refresh_token():
    return secrets.token_hex(32)


# ---------------- VERIFY TOKEN ----------------
def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None