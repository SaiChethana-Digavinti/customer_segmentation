# ============================================================
# ANALYSIS HISTORY SERVICE
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

import io
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, String

from app.database.models import AnalysisHistory, User, Customer
from app.services.audit_service import log_activity
from app.services.report_service import (
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
    generate_docx_report,
    generate_json_report,
)

logger = logging.getLogger("history_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ============================================================
# RECORD / AUTO-SAVE ANALYSIS HISTORY
# ============================================================

def record_analysis_history(
    db: Session,
    user: Optional[User],
    customer_id: Any,
    customer_data: Optional[Dict[str, Any]],
    ai_message: str,
    marketing_strategy: Optional[str] = None,
    recommended_action: Optional[str] = None,
) -> AnalysisHistory:
    """
    Automatically persist customer analysis and AI recommendation to the database.
    Includes deduplication check: if a record for this customer was created within
    the last 60 seconds by the same user with identical recommendation, update or return it.
    """
    cid_str = str(customer_id).strip()
    uid = user.id if user else None
    username = user.username if user else "anonymous"

    # Normalize customer dictionary
    c = customer_data or {}

    # Extract customer attributes
    customer_name = str(
        c.get("customer_name") or
        c.get("name") or
        f"Customer #{cid_str}"
    ).strip()

    segment = str(c.get("segment") or c.get("Segment") or "Standard").strip()
    strategy = str(marketing_strategy or c.get("marketing_strategy") or c.get("Marketing_Strategy") or "").strip()
    action = str(recommended_action or c.get("recommended_action") or c.get("Recommended_Action") or "").strip()

    # RFM & segmentation values
    segmentation_data = {
        "recency": int(c.get("recency") or c.get("Recency") or 0),
        "frequency": int(c.get("frequency") or c.get("Frequency") or 0),
        "monetary": float(c.get("monetary") or c.get("Monetary") or 0.0),
        "rfm_score": str(c.get("rfm_score") or c.get("RFM_Score") or "-"),
        "rfm_total": int(c.get("rfm_total") or c.get("RFM_Total") or 0),
        "priority": str(c.get("priority") or c.get("Priority") or "Medium"),
        "campaign": str(c.get("campaign") or c.get("Campaign") or "General Retention"),
        "cluster": c.get("cluster"),
        "silhouette_score": c.get("silhouette_score"),
    }

    # Additional attributes (age, gender, location) if present
    customer_details = {
        "age": c.get("age"),
        "gender": c.get("gender"),
        "location": c.get("location") or c.get("country") or "Global",
        "customer_id": cid_str,
        "customer_name": customer_name,
    }

    # Deduplication check (within 60 seconds)
    recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
    existing_query = db.query(AnalysisHistory).filter(
        AnalysisHistory.customer_id == cid_str,
        AnalysisHistory.analysis_date >= recent_cutoff
    )
    if uid is not None:
        existing_query = existing_query.filter(AnalysisHistory.user_id == uid)

    recent_record = existing_query.first()
    if recent_record:
        # Update existing record rather than creating a duplicate
        recent_record.ai_recommendation = ai_message
        recent_record.marketing_strategy = strategy
        recent_record.recommended_action = action
        recent_record.segmentation_data = segmentation_data
        recent_record.customer_details = customer_details
        recent_record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(recent_record)
        logger.info(f"Updated existing recent analysis history #{recent_record.id} for customer {cid_str}")
        return recent_record

    # Create new analysis history record
    history_record = AnalysisHistory(
        user_id=uid,
        customer_id=cid_str,
        customer_name=customer_name,
        analysis_date=datetime.utcnow(),
        customer_details=customer_details,
        segmentation_data=segmentation_data,
        predicted_segment=segment,
        segment_explanation=f"Customer classified into '{segment}' cohort based on RFM score ({segmentation_data['rfm_score']}).",
        ai_recommendation=ai_message,
        marketing_strategy=strategy,
        recommended_action=action,
        report_status="COMPLETED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(history_record)
    db.commit()
    db.refresh(history_record)

    log_activity(
        db=db,
        username=username,
        action="ANALYSIS_SAVED",
        details=f"Saved customer analysis history for customer ID {cid_str} (Segment: {segment})",
        status="SUCCESS",
        user_id=uid,
    )

    logger.info(f"Successfully recorded analysis history #{history_record.id} for customer {cid_str}")
    return history_record


# ============================================================
# GET ANALYSIS HISTORY LIST (FILTERED & PAGINATED)
# ============================================================

def get_history_records(
    db: Session,
    current_user: User,
    search: Optional[str] = None,
    segment: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Retrieve paginated analysis history records based on search, filters,
    and the user's role (Admin sees all; Analyst/User sees only own records).
    """
    query = db.query(AnalysisHistory)

    # 1. Role-based scoping
    is_admin = current_user.role.lower() == "admin"
    if not is_admin:
        query = query.filter(AnalysisHistory.user_id == current_user.id)

    # 2. Search query (Customer ID, Customer Name, or Analysis ID)
    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AnalysisHistory.customer_id.ilike(s),
                AnalysisHistory.customer_name.ilike(s),
                cast(AnalysisHistory.id, String).ilike(s)
            )
        )

    # 3. Segment filter
    if segment and segment.strip() and segment.strip().lower() != "all":
        query = query.filter(
            AnalysisHistory.predicted_segment.ilike(f"%{segment.strip()}%")
        )

    # 4. Date range filter
    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip()[:10], "%Y-%m-%d")
            query = query.filter(AnalysisHistory.analysis_date >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(end_date.strip()[:10], "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AnalysisHistory.analysis_date < end_dt)
        except ValueError:
            pass

    # 5. Recommendation keyword / type filter
    if recommendation_type and recommendation_type.strip():
        rt = f"%{recommendation_type.strip()}%"
        query = query.filter(
            or_(
                AnalysisHistory.ai_recommendation.ilike(rt),
                AnalysisHistory.marketing_strategy.ilike(rt),
                AnalysisHistory.recommended_action.ilike(rt)
            )
        )

    # Order newest first
    query = query.order_by(AnalysisHistory.id.desc())

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    current_page = max(1, min(page, total_pages)) if total > 0 else 1
    offset = (current_page - 1) * page_size

    records_raw = query.offset(offset).limit(page_size).all()

    # Pre-fetch user usernames for display
    user_ids = {r.user_id for r in records_raw if r.user_id is not None}
    users_map = {}
    if user_ids:
        users = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        users_map = {u.id: u.username for u in users}

    formatted_records = []
    for r in records_raw:
        # Create concise snippet for table
        snippet = ""
        if r.ai_recommendation:
            clean_rec = " ".join(r.ai_recommendation.split())
            snippet = clean_rec[:90] + "..." if len(clean_rec) > 90 else clean_rec
        elif r.marketing_strategy:
            snippet = r.marketing_strategy[:90]

        formatted_records.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": users_map.get(r.user_id, "System / Seeded"),
            "customer_id": r.customer_id,
            "customer_name": r.customer_name or f"Customer #{r.customer_id}",
            "analysis_date": r.analysis_date,
            "predicted_segment": r.predicted_segment or "Unassigned",
            "ai_recommendation_snippet": snippet,
            "marketing_strategy": r.marketing_strategy,
            "recommended_action": r.recommended_action,
            "report_status": r.report_status or "COMPLETED",
        })

    return {
        "total": total,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "records": formatted_records,
    }


# ============================================================
# GET SINGLE ANALYSIS DETAIL (WITH ROLE CHECK)
# ============================================================

def get_history_by_id(
    db: Session,
    history_id: int,
    current_user: User,
) -> Dict[str, Any]:
    """
    Retrieve single historical analysis record by ID.
    Strictly verifies ownership if user is not an Admin.
    IMPORTANT: Returns the previously stored snapshot without calling AI.
    """
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis history record #{history_id} not found."
        )

    # Security check: Analyst cannot view another user's record
    is_admin = current_user.role.lower() == "admin"
    if not is_admin and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this analysis record."
        )

    owner = db.query(User).filter(User.id == record.user_id).first() if record.user_id else None

    return {
        "id": record.id,
        "user_id": record.user_id,
        "username": owner.username if owner else "System",
        "customer_id": record.customer_id,
        "customer_name": record.customer_name or f"Customer #{record.customer_id}",
        "analysis_date": record.analysis_date,
        "customer_details": record.customer_details or {},
        "segmentation_data": record.segmentation_data or {},
        "predicted_segment": record.predicted_segment or "Unknown",
        "segment_explanation": record.segment_explanation or "",
        "ai_recommendation": record.ai_recommendation or "No AI recommendation was saved for this analysis.",
        "marketing_strategy": record.marketing_strategy or "",
        "recommended_action": record.recommended_action or "",
        "report_status": record.report_status or "COMPLETED",
        "created_at": record.created_at,
    }


# ============================================================
# DELETE ANALYSIS RECORD (WITH CONFIRMATION & AUDIT)
# ============================================================

def delete_history_record(
    db: Session,
    history_id: int,
    current_user: User,
) -> bool:
    """
    Delete an analysis record with role authorization and audit logging.
    """
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis history record #{history_id} not found."
        )

    # Security check
    is_admin = current_user.role.lower() == "admin"
    if not is_admin and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to delete this analysis record."
        )

    cid = record.customer_id
    db.delete(record)
    db.commit()

    log_activity(
        db=db,
        username=current_user.username,
        action="DELETE_ANALYSIS_HISTORY",
        details=f"Deleted analysis history record #{history_id} for customer ID {cid}",
        status="SUCCESS",
        user_id=current_user.id,
    )

    logger.info(f"User {current_user.username} deleted analysis history #{history_id}")
    return True


# ============================================================
# GENERATE HISTORICAL REPORT (MULTI-FORMAT EXPORT)
# ============================================================

def generate_historical_report(
    db: Session,
    history_id: int,
    file_format: str,
    current_user: User,
) -> Tuple[Any, str, str]:
    """
    Export the historical analysis in the requested format (csv, xlsx, pdf, docx, json).
    Guarantees that the report contains the saved historical analysis data, NOT newly generated data.
    """
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis history record #{history_id} not found."
        )

    # Security check
    is_admin = current_user.role.lower() == "admin"
    if not is_admin and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to export this analysis record."
        )

    seg_data = record.segmentation_data or {}
    cust_details = record.customer_details or {}

    # Format customer dictionary expected by report_service
    customer_dict = {
        "customer_id": record.customer_id,
        "customer_name": record.customer_name or cust_details.get("customer_name") or f"Customer #{record.customer_id}",
        "segment": record.predicted_segment or "Unknown",
        "recency": seg_data.get("recency", 0),
        "frequency": seg_data.get("frequency", 0),
        "monetary": seg_data.get("monetary", 0.0),
        "rfm_score": seg_data.get("rfm_score", "-"),
        "rfm_total": seg_data.get("rfm_total", 0),
        "priority": seg_data.get("priority", "Medium"),
        "campaign": seg_data.get("campaign", "General Campaign"),
        "marketing_strategy": record.marketing_strategy or seg_data.get("marketing_strategy", ""),
        "recommended_action": record.recommended_action or seg_data.get("recommended_action", ""),
        "ai_message": record.ai_recommendation or "",
    }

    filter_info = {
        "title": f"Historical Analysis Report — Customer #{record.customer_id}",
        "analysis_id": record.id,
        "analysis_date": record.analysis_date.strftime("%Y-%m-%d %H:%M:%S") if record.analysis_date else "",
        "segment": record.predicted_segment or "All",
        "priority": seg_data.get("priority", "All"),
    }

    fmt = file_format.lower().strip().lstrip(".")
    customers_list = [customer_dict]

    if fmt == "csv":
        content, _ = generate_csv_report(customers_list, filter_info)
        filename = f"analysis_history_customer_{record.customer_id}_id{record.id}.csv"
        media_type = "text/csv; charset=utf-8"
        body = content.encode("utf-8") if isinstance(content, str) else content

    elif fmt in ("xlsx", "excel"):
        body, _ = generate_excel_report(customers_list, filter_info)
        filename = f"analysis_history_customer_{record.customer_id}_id{record.id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif fmt == "pdf":
        body, _ = generate_pdf_report(customers_list, filter_info)
        filename = f"analysis_history_customer_{record.customer_id}_id{record.id}.pdf"
        media_type = "application/pdf"

    elif fmt in ("docx", "word"):
        body, _ = generate_docx_report(customers_list, filter_info)
        filename = f"analysis_history_customer_{record.customer_id}_id{record.id}.docx"
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif fmt == "json":
        # Enrich JSON with full historical details
        json_payload = {
            "analysis_id": record.id,
            "export_date": datetime.utcnow().isoformat(),
            "analysis_date": record.analysis_date.isoformat() if record.analysis_date else None,
            "customer_id": record.customer_id,
            "customer_name": record.customer_name,
            "customer_details": cust_details,
            "segmentation": {
                "predicted_segment": record.predicted_segment,
                "segment_explanation": record.segment_explanation,
                "recency": seg_data.get("recency", 0),
                "frequency": seg_data.get("frequency", 0),
                "monetary": seg_data.get("monetary", 0.0),
                "rfm_score": seg_data.get("rfm_score", "-"),
                "rfm_total": seg_data.get("rfm_total", 0),
                "priority": seg_data.get("priority", "Medium"),
                "campaign": seg_data.get("campaign", "General Campaign"),
            },
            "ai_recommendation": {
                "ai_message": record.ai_recommendation,
                "marketing_strategy": record.marketing_strategy,
                "recommended_action": record.recommended_action,
            },
            "report_status": record.report_status,
        }
        content = json.dumps(json_payload, indent=2, ensure_ascii=False)
        filename = f"analysis_history_customer_{record.customer_id}_id{record.id}.json"
        media_type = "application/json; charset=utf-8"
        body = content.encode("utf-8")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format '{file_format}'. Supported formats: csv, xlsx, pdf, docx, json."
        )

    log_activity(
        db=db,
        username=current_user.username,
        action="EXPORT_ANALYSIS_HISTORY",
        details=f"Exported analysis history #{history_id} as {fmt.upper()}",
        status="SUCCESS",
        user_id=current_user.id,
    )

    return body, filename, media_type


# ============================================================
# SEED DEFAULT ANALYSIS HISTORY (DEMO RECORDS)
# ============================================================

def seed_default_history(db: Session) -> None:
    """
    Seed initial analysis history records for admin and analyst accounts
    if the table is currently empty, ensuring immediate demonstration
    of search, filtering, viewing, and downloading.
    """
    try:
        count = db.query(AnalysisHistory).count()
        if count > 0:
            return

        admin_user = db.query(User).filter(User.username == "admin").first()
        analyst_user = db.query(User).filter(User.username == "analyst").first()

        admin_id = admin_user.id if admin_user else None
        analyst_id = analyst_user.id if analyst_user else None

        now = datetime.utcnow()

        sample_records = [
            # Records for Admin
            {
                "user_id": admin_id,
                "customer_id": "1007",
                "customer_name": "Eleanor Vance (VIP)",
                "analysis_date": now - timedelta(days=2, hours=3),
                "customer_details": {"age": 34, "gender": "Female", "location": "New York, USA"},
                "segmentation_data": {
                    "recency": 16,
                    "frequency": 2,
                    "monetary": 1600.0,
                    "rfm_score": "425",
                    "rfm_total": 11,
                    "priority": "High",
                    "campaign": "VIP Rewards Campaign",
                    "cluster": 0,
                    "silhouette_score": 0.68,
                },
                "predicted_segment": "Champions",
                "segment_explanation": "Champions are high-spend, loyal customers who purchase frequently and recently.",
                "ai_recommendation": (
                    "• Strategic Objective: Preserve Tier-1 loyalty and drive organic brand advocacy.\n"
                    "• Key Action: Invite to exclusive private previews and offer early-access VIP product drops.\n"
                    "• Recommended Messaging: 'As our top valued member, enjoy complimentary priority shipping and VIP concierge service.'\n"
                    "• Expected ROI: 28% increase in annual customer lifetime value (LTV)."
                ),
                "marketing_strategy": "Reward and retain high-value customers",
                "recommended_action": "Offer VIP rewards and early access",
                "report_status": "COMPLETED",
            },
            {
                "user_id": admin_id,
                "customer_id": "1010",
                "customer_name": "Marcus Aurelius",
                "analysis_date": now - timedelta(days=1, hours=6),
                "customer_details": {"age": 42, "gender": "Male", "location": "Chicago, USA"},
                "segmentation_data": {
                    "recency": 6,
                    "frequency": 2,
                    "monetary": 950.0,
                    "rfm_score": "515",
                    "rfm_total": 11,
                    "priority": "High",
                    "campaign": "VIP Rewards Campaign",
                    "cluster": 0,
                    "silhouette_score": 0.64,
                },
                "predicted_segment": "Champions",
                "segment_explanation": "Recent high-value customer with exceptionally low recency (active this week).",
                "ai_recommendation": (
                    "• Strategic Objective: Accelerate repeat purchase cadence through curated upsells.\n"
                    "• Key Action: Deploy automated thank-you note with milestone loyalty bonus.\n"
                    "• Recommended Channel: High-priority email + SMS notification."
                ),
                "marketing_strategy": "Reward and retain high-value customers",
                "recommended_action": "Offer VIP rewards and early access",
                "report_status": "COMPLETED",
            },
            # Records for Analyst
            {
                "user_id": analyst_id,
                "customer_id": "1013",
                "customer_name": "Sophia Bennett",
                "analysis_date": now - timedelta(days=3, hours=8),
                "customer_details": {"age": 29, "gender": "Female", "location": "San Francisco, USA"},
                "segmentation_data": {
                    "recency": 21,
                    "frequency": 2,
                    "monetary": 1400.0,
                    "rfm_score": "415",
                    "rfm_total": 10,
                    "priority": "High",
                    "campaign": "VIP Rewards Campaign",
                    "cluster": 0,
                    "silhouette_score": 0.65,
                },
                "predicted_segment": "Champions",
                "segment_explanation": "High monetary contributor with strong loyalty metrics across the recent quarter.",
                "ai_recommendation": (
                    "• Strategic Objective: Boost order basket size with personalized cross-category bundles.\n"
                    "• Key Action: Feature high-affinity accessory recommendations on dashboard login.\n"
                    "• Campaign Target: Luxury upgrade and premium loyalty tier."
                ),
                "marketing_strategy": "Reward and retain high-value customers",
                "recommended_action": "Offer VIP rewards and early access",
                "report_status": "COMPLETED",
            },
            {
                "user_id": analyst_id,
                "customer_id": "1002",
                "customer_name": "David Miller",
                "analysis_date": now - timedelta(hours=18),
                "customer_details": {"age": 38, "gender": "Male", "location": "Austin, USA"},
                "segmentation_data": {
                    "recency": 75,
                    "frequency": 1,
                    "monetary": 320.0,
                    "rfm_score": "212",
                    "rfm_total": 5,
                    "priority": "Medium",
                    "campaign": "Re-engagement Campaign",
                    "cluster": 1,
                    "silhouette_score": 0.52,
                },
                "predicted_segment": "At Risk",
                "segment_explanation": "Customer recency has deteriorated over 75 days. Needs active win-back intervention.",
                "ai_recommendation": (
                    "• Strategic Objective: Prevent imminent churn and reignite brand affinity.\n"
                    "• Key Action: Send targeted 'We miss you' coupon with 15% discount valid for 7 days.\n"
                    "• Recommended Copy: 'It's been a while, David! Here is an exclusive 15% voucher on your favorite items.'\n"
                    "• Expected Churn Reduction: 18% recovery rate."
                ),
                "marketing_strategy": "Re-engage customers with win-back promotions",
                "recommended_action": "Send win-back email with discount",
                "report_status": "COMPLETED",
            },
            {
                "user_id": analyst_id,
                "customer_id": "1005",
                "customer_name": "Aria Chen",
                "analysis_date": now - timedelta(hours=4),
                "customer_details": {"age": 25, "gender": "Female", "location": "Seattle, USA"},
                "segmentation_data": {
                    "recency": 12,
                    "frequency": 3,
                    "monetary": 780.0,
                    "rfm_score": "534",
                    "rfm_total": 12,
                    "priority": "Medium",
                    "campaign": "Upsell & Loyalty Campaign",
                    "cluster": 2,
                    "silhouette_score": 0.59,
                },
                "predicted_segment": "Potential Loyalists",
                "segment_explanation": "High engagement frequency and low recency. High probability to transition to Champions cohort.",
                "ai_recommendation": (
                    "• Strategic Objective: Nurture frequent shopper into long-term brand ambassador.\n"
                    "• Key Action: Introduce point-multiplier promotions for multi-item orders.\n"
                    "• Recommended Strategy: Community invitation and beta-tester program."
                ),
                "marketing_strategy": "Nurture into champions with loyalty incentives",
                "recommended_action": "Offer loyalty program membership",
                "report_status": "COMPLETED",
            },
        ]

        for s in sample_records:
            item = AnalysisHistory(
                user_id=s["user_id"],
                customer_id=s["customer_id"],
                customer_name=s["customer_name"],
                analysis_date=s["analysis_date"],
                customer_details=s["customer_details"],
                segmentation_data=s["segmentation_data"],
                predicted_segment=s["predicted_segment"],
                segment_explanation=s["segment_explanation"],
                ai_recommendation=s["ai_recommendation"],
                marketing_strategy=s["marketing_strategy"],
                recommended_action=s["recommended_action"],
                report_status=s["report_status"],
                created_at=s["analysis_date"],
                updated_at=s["analysis_date"],
            )
            db.add(item)

        db.commit()
        print("📜 Seeded initial sample Analysis History records.")

    except Exception as exc:
        db.rollback()
        print(f"⚠️ Warning during analysis history seeding: {exc}")
