from typing import Dict
import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from pymongo import MongoClient

from .schemas.auth_models import UserSignup, UserLogin


MONGO_URI = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client.get_default_database() if client else None

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)


def create_user(user: UserSignup) -> Dict:
    """Create a new user in MongoDB. Returns user dict (without password)."""
    users = db.users
    existing = users.find_one({"email": user.email.lower()})
    if existing:
        raise ValueError("Email already registered")

    hashed = _hash_password(user.password)
    doc = {
        "email": user.email.lower(),
        "password": hashed,  # stored as bytes
        "full_name": user.full_name,
        "created_at": datetime.utcnow(),
    }
    res = users.insert_one(doc)
    return {"id": str(res.inserted_id), "email": doc["email"], "full_name": doc["full_name"]}


def _create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": subject}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(login: UserLogin) -> Dict:
    """Verify credentials and return access token + user info."""
    users = db.users
    user = users.find_one({"email": login.email.lower()})
    if not user:
        raise ValueError("Invalid credentials")

    hashed = user.get("password")
    # pymongo may store binary data under Binary; ensure bytes
    if isinstance(hashed, memoryview):
        hashed = bytes(hashed)

    if not _verify_password(login.password, hashed):
        raise ValueError("Invalid credentials")

    access_token = _create_access_token(subject=login.email.lower())
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user["email"], "full_name": user.get("full_name")}}

