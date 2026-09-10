# ============================================================
# AUDIT SERVICE
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import AuditLog


def log_activity(
    db: Session,
    username: str,
    action: str,
    details: Optional[str] = "",
    status: str = "SUCCESS",
    user_id: Optional[int] = None
) -> None:
    """
    Record an administrative or security event to the audit_logs table.
    """
    try:
        log_entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            details=details,
            status=status,
        )
        db.add(log_entry)
        db.commit()
    except Exception as err:
        db.rollback()
        print(f"⚠️ Failed to write audit log: {err}")
