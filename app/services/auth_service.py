# ============================================================
# AUTHENTICATION SERVICE
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from argon2 import PasswordHasher
try:
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
except ImportError:
    from argon2.exceptions import VerifyMismatchError, InvalidHash as InvalidHashError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User


# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "customer-ai-secret-key-enterprise-2026-secure-jwt-token"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

password_hasher = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password using Argon2id.
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against an Argon2 hash.
    """
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        return False


# ============================================================
# JWT TOKEN MANAGEMENT
# ============================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a signed JWT access token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


# ============================================================
# DEPENDENCIES (GET CURRENT USER & ROLE CHECKS)
# ============================================================

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current authenticated user from Bearer token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    username: Optional[str] = payload.get("sub")
    if not username:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optionally retrieve current authenticated user without throwing 401.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    return db.query(User).filter(User.username == username).first()


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Enforce that current authenticated user has 'admin' role.
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to access this resource."
        )

    return current_user


# ============================================================
# DEFAULT USER SEEDING
# ============================================================

def seed_default_users(db: Session) -> None:
    """
    Ensure default admin and analyst accounts exist for immediate use.
    """
    try:
        # Check admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@customerai.local",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(admin_user)
            print("👤 Seeded default admin account (username: admin)")

        # Check analyst user
        analyst_user = db.query(User).filter(User.username == "analyst").first()
        if not analyst_user:
            analyst_user = User(
                username="analyst",
                email="analyst@customerai.local",
                full_name="Data Analyst",
                hashed_password=hash_password("user123"),
                role="analyst",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(analyst_user)
            print("👤 Seeded default analyst account (username: analyst)")

        db.commit()

    except Exception as error:
        db.rollback()
        print(f"⚠️ Warning during user seeding: {error}")
