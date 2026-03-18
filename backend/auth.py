import bcrypt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of the password."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Return as a string for database storage
    return hashed_password.decode('utf-8')


JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "43200"))  # 30 days

def _jwt_secret() -> str:
    # In production set JWT_SECRET in env
    return os.getenv("JWT_SECRET", "dev-change-me")

def create_access_token(claims: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or JWT_EXPIRES_MINUTES)
    payload = {
        **claims,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e