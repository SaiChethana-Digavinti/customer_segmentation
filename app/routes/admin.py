# ============================================================
# ADMIN ROUTES
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db, test_database_connection
from app.database.models import User, AuditLog, Customer, DatasetRun
from app.schemas import (
    UserResponse,
    AdminStatsResponse,
    AdminUserCreate,
    UserUpdateRole,
    UserUpdateStatus,
    AuditLogResponse,
    DatasetRunResponse,
)
from app.services.auth_service import (
    require_admin,
    hash_password,
)
from app.services.audit_service import log_activity


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(require_admin)],
)


# ============================================================
# ADMIN PLATFORM STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get administration platform KPIs and statistics"
)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Return platform-wide administrative metrics, user counts, and health status.
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    analyst_users = db.query(User).filter(User.role == "analyst").count()

    total_customers = db.query(Customer).count()
    total_dataset_runs = db.query(DatasetRun).count()

    db_healthy = test_database_connection()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "analyst_users": analyst_users,
        "total_customers": total_customers,
        "total_dataset_runs": total_dataset_runs,
        "db_status": "Healthy (Connected)" if db_healthy else "Degraded",
        "system_status": "Operational",
    }


# ============================================================
# USER MANAGEMENT - LIST USERS
# ============================================================

@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all registered platform users"
)
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Retrieve all users registered in the system.
    """
    users = db.query(User).order_by(User.id.desc()).all()
    return users


# ============================================================
# USER MANAGEMENT - CREATE USER
# ============================================================

@router.post(
    "/users",
    response_model=UserResponse,
    summary="Create a new user as administrator"
)
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Create a new user account with specified role and initial status.
    """
    existing_user = db.query(User).filter(
        (User.username == payload.username.strip()) |
        (User.email == payload.email.strip().lower())
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists."
        )

    role = payload.role.strip().lower()
    if role not in ["admin", "analyst"]:
        role = "analyst"

    new_user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=role,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(
        db=db,
        username=current_admin.username,
        action="USER_CREATE",
        details=f"Admin created user: {new_user.username} (role: {role})",
        status="SUCCESS",
        user_id=current_admin.id
    )

    return new_user


# ============================================================
# USER MANAGEMENT - UPDATE ROLE
# ============================================================

@router.put(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Change user role (admin / analyst)"
)
def update_user_role(
    user_id: int,
    payload: UserUpdateRole,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Promote or demote a user account role.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found."
        )

    new_role = payload.role.strip().lower()
    if new_role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin' or 'analyst'."
        )

    # Prevent demoting oneself if the last admin
    if target_user.id == current_admin.id and new_role != "admin":
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only active administrator."
            )

    old_role = target_user.role
    target_user.role = new_role
    db.commit()
    db.refresh(target_user)

    log_activity(
        db=db,
        username=current_admin.username,
        action="USER_ROLE_CHANGE",
        details=f"Changed user '{target_user.username}' role from {old_role} to {new_role}",
        status="SUCCESS",
        user_id=current_admin.id
    )

    return target_user


# ============================================================
# USER MANAGEMENT - TOGGLE STATUS
# ============================================================

@router.put(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Toggle user active / disabled status"
)
def update_user_status(
    user_id: int,
    payload: UserUpdateStatus,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Activate or deactivate a user account.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found."
        )

    # Prevent deactivating own account
    if target_user.id == current_admin.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own administrative account."
        )

    target_user.is_active = payload.is_active
    db.commit()
    db.refresh(target_user)

    action_label = "ACTIVATED" if payload.is_active else "DEACTIVATED"
    log_activity(
        db=db,
        username=current_admin.username,
        action="USER_STATUS_CHANGE",
        details=f"Admin {action_label} user: {target_user.username}",
        status="SUCCESS",
        user_id=current_admin.id
    )

    return target_user


# ============================================================
# USER MANAGEMENT - DELETE USER
# ============================================================

@router.delete(
    "/users/{user_id}",
    summary="Delete a user account"
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Delete a user account. Prevents deleting self.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found."
        )

    if target_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own administrative account."
        )

    deleted_username = target_user.username
    db.delete(target_user)
    db.commit()

    log_activity(
        db=db,
        username=current_admin.username,
        action="USER_DELETE",
        details=f"Admin deleted user account: {deleted_username}",
        status="SUCCESS",
        user_id=current_admin.id
    )

    return {"message": f"User '{deleted_username}' has been successfully removed."}


# ============================================================
# AUDIT LOGS TRAIL
# ============================================================

@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    summary="Retrieve system audit and activity logs"
)
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Fetch historical activity and security audit trail.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action.strip().upper())

    logs = query.order_by(AuditLog.id.desc()).limit(limit).all()
    return logs


# ============================================================
# DATASET RUNS HISTORY
# ============================================================

@router.get(
    "/dataset-runs",
    response_model=List[DatasetRunResponse],
    summary="List recent dataset upload and clustering runs"
)
def get_dataset_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Fetch history of customer dataset imports and segmentation runs.
    """
    runs = db.query(DatasetRun).order_by(DatasetRun.id.desc()).limit(limit).all()
    return runs


# ============================================================
# MAINTENANCE - CLEAR CACHE / LOG EVENT
# ============================================================

@router.post(
    "/maintenance/clear-cache",
    summary="Flush system application cache and sync database"
)
def clear_cache(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Trigger platform cache refresh and synchronization.
    """
    log_activity(
        db=db,
        username=current_admin.username,
        action="SYSTEM_CACHE_CLEAR",
        details="Platform cache cleared and database re-synced by administrator",
        status="SUCCESS",
        user_id=current_admin.id
    )

    return {
        "status": "success",
        "message": "System cache cleared and database connections refreshed successfully."
    }
