import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from passlib.context import CryptContext
from app.core.config import settings

SECRET_KEY = settings.APP_SECRET_KEY
ALGORITHM = "HS256"

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

get_password_hash = hash_password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Retrieves authenticated user from session token cookie or Authorization header.
    If no token is provided, returns None (unauthenticated state).
    """
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if token:
        payload = decode_access_token(token)
        if payload and "email" in payload:
            from app.services.mongo_client import mongo_client
            # Fetch user from MongoDB
            if mongo_client._connected:
                user = mongo_client.db.users.find_one({"email": payload["email"]})
                if user:
                    # Convert ObjectId to string for easy serialization across the app
                    user["id"] = str(user.pop("_id"))
                    role = user.get("role", "student")
                    default_avatar = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=256"
                    if role == "faculty":
                        default_avatar = "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=256"
                    elif role == "admin":
                        default_avatar = "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?q=80&w=256"
                    user["avatar"] = user.get("profile_picture") or default_avatar
                    return user
            return payload
    return None
