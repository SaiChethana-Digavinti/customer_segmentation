# ============================================================
# AUTHENTICATION ROUTES
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.services.audit_service import log_activity


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER USER
# ============================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new user account"
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new platform user with hashed password and return access token.
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == payload.username.strip()) |
        (User.email == payload.email.strip().lower())
    ).first()

    if existing_user:
        if existing_user.username == payload.username.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken. Please choose another."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

    # Normalize role
    role = payload.role.strip().lower() if payload.role else "analyst"
    if role not in ["admin", "analyst"]:
        role = "analyst"

    new_user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Record audit log
    log_activity(
        db=db,
        username=new_user.username,
        action="REGISTER",
        details=f"New user registered with role: {role}",
        status="SUCCESS",
        user_id=new_user.id
    )

    # Generate JWT Token
    token = create_access_token(data={"sub": new_user.username, "role": new_user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }


# ============================================================
# LOGIN USER
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in with username and password"
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials, update last login time, and return JWT token.
    """
    identifier = payload.username.strip()

    # Allow login with either username or email
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        log_activity(
            db=db,
            username=identifier,
            action="LOGIN_FAILED",
            details="Invalid credentials provided",
            status="FAILED"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    if not user.is_active:
        log_activity(
            db=db,
            username=user.username,
            action="LOGIN_BLOCKED",
            details="Attempted login on deactivated account",
            status="WARNING",
            user_id=user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact your system administrator."
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    log_activity(
        db=db,
        username=user.username,
        action="LOGIN",
        details=f"User signed in successfully (role: {user.role})",
        status="SUCCESS",
        user_id=user.id
    )

    token = create_access_token(data={"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


# ============================================================
# CURRENT USER PROFILE (/auth/me)
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Return currently authenticated user's profile information.
    """
    return current_user


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
    summary="Sign out user session"
)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log user sign-out event. Client will discard the JWT token.
    """
    log_activity(
        db=db,
        username=current_user.username,
        action="LOGOUT",
        details="User signed out",
        status="SUCCESS",
        user_id=current_user.id
    )
    return {"message": "Successfully logged out."}
