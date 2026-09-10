import csv
import io
import logging
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.services.auth_service import get_optional_user
from app.services.history_service import record_analysis_history

logger = logging.getLogger("customers_routes")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

from app.schemas import (
    CustomerResponse,
    SegmentSummary,
    CustomerStatisticsResponse,
    DashboardOverviewResponse,
    CampaignSummaryResponse,
    PrioritySummaryResponse,
    AIRecommendationResponse,
)

from app.services.customer_services import (
    get_all_customers,
    get_customer_by_id,
    get_segment_summary,
    get_customer_statistics,
    get_dashboard_overview,
    get_campaign_summary,
    get_priority_summary,
    get_customers_by_segment,
    get_customers_by_priority,
    search_customers,
)

from app.services.ai_service import (
    generate_ai_recommendation,
)

from app.services.report_service import (
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
    generate_docx_report,
    generate_json_report,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


# ============================================================
# CUSTOMER HEALTH
# ============================================================

@router.get(
    "/health",
    summary="Customer service health check",
)
def customer_health():
    """
    Check whether the customer service is available.
    """

    return {
        "status": "healthy",
        "service": "customer-service",
    }


# ============================================================
# CUSTOMER STATISTICS
# ============================================================

@router.get(
    "/statistics",
    response_model=CustomerStatisticsResponse,
    summary="Get customer statistics",
)
def customer_statistics():
    """
    Return overall customer statistics.
    """

    try:
        result = get_customer_statistics()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Customer statistics not found",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve customer statistics: {str(exc)}",
        )


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================

@router.get(
    "/dashboard/overview",
    response_model=DashboardOverviewResponse,
    summary="Get dashboard overview",
)
def dashboard_overview():
    """
    Return aggregated information used by the dashboard.
    """

    try:
        result = get_dashboard_overview()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Dashboard overview not found",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve dashboard overview: {str(exc)}",
        )


# ============================================================
# SEGMENT SUMMARY
# ============================================================

@router.get(
    "/segments/summary",
    response_model=List[SegmentSummary],
    summary="Get customer segment summary",
)
def segment_summary():
    """
    Return customer counts and metrics grouped by segment.
    """

    try:
        result = get_segment_summary()

        if result is None:
            return []

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve segment summary: {str(exc)}",
        )


# ============================================================
# CAMPAIGN SUMMARY
# ============================================================

@router.get(
    "/campaigns/summary",
    response_model=List[CampaignSummaryResponse],
    summary="Get campaign summary",
)
def campaign_summary():
    """
    Return marketing campaign statistics.
    """

    try:
        result = get_campaign_summary()

        if result is None:
            return []

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve campaign summary: {str(exc)}",
        )


# ============================================================
# PRIORITY SUMMARY
# ============================================================

@router.get(
    "/priority/summary",
    response_model=List[PrioritySummaryResponse],
    summary="Get customer priority summary",
)
def priority_summary():
    """
    Return customer counts grouped by priority.
    """

    try:
        result = get_priority_summary()

        if result is None:
            return []

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve priority summary: {str(exc)}",
        )


# ============================================================
# SEARCH CUSTOMERS
# ============================================================

@router.get(
    "/search",
    response_model=List[CustomerResponse],
    summary="Search customers",
)
def search_customer_records(
    query: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="Customer ID, segment, campaign or priority",
    ),
):
    """
    Search customers using customer ID, segment,
    campaign or priority.
    """

    try:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty",
            )

        result = search_customers(cleaned_query)

        if result is None:
            return []

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to search customers: {str(exc)}",
        )


# ============================================================
# FILTER BY SEGMENT
# ============================================================

@router.get(
    "/filter/segment",
    response_model=List[CustomerResponse],
    summary="Filter customers by segment",
)
def filter_by_segment(
    segment: str = Query(
        ...,
        min_length=1,
        max_length=100,
    ),
):
    """
    Return customers belonging to a particular segment.
    """

    try:
        cleaned_segment = segment.strip()

        if not cleaned_segment:
            raise HTTPException(
                status_code=400,
                detail="Segment cannot be empty",
            )

        result = get_customers_by_segment(
            cleaned_segment
        )

        if result is None:
            return []

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to filter customers by segment: {str(exc)}",
        )


# ============================================================
# FILTER BY PRIORITY
# ============================================================

@router.get(
    "/filter/priority",
    response_model=List[CustomerResponse],
    summary="Filter customers by priority",
)
def filter_by_priority(
    priority: str = Query(
        ...,
        min_length=1,
        max_length=50,
    ),
):
    """
    Return customers belonging to a particular priority level.
    """

    try:
        cleaned_priority = priority.strip()

        if not cleaned_priority:
            raise HTTPException(
                status_code=400,
                detail="Priority cannot be empty",
            )

        result = get_customers_by_priority(
            cleaned_priority
        )

        if result is None:
            return []

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to filter customers by priority: {str(exc)}",
        )


# ============================================================
# GET ALL CUSTOMERS
# ============================================================

@router.get(
    "/",
    response_model=List[CustomerResponse],
    summary="Get all customers",
)
def get_customers():
    """
    Return all customers stored in the database.
    """

    try:
        result = get_all_customers()

        if result is None:
            return []

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve customers: {str(exc)}",
        )


# ============================================================
# GET CUSTOMER BY DATABASE ID
# ============================================================

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
)
def get_customer(
    customer_id: int,
):
    """
    Return a single customer using the internal database ID.
    """

    try:
        customer = get_customer_by_id(
            customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found",
            )

        return customer

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve customer: {str(exc)}",
        )


# ============================================================
# AI RECOMMENDATION
# ============================================================

@router.get(
    "/{customer_id}/ai-recommendation",
    response_model=AIRecommendationResponse,
    summary="Generate AI marketing recommendation",
)
def ai_recommendation(
    customer_id: int,
    response: Response,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Generate a Gemini-powered marketing recommendation
    for a specific customer and auto-save the result into Analysis History.
    """

    try:
        start_time = time.perf_counter()

        # ----------------------------------------------------
        # Fetch customer
        # ----------------------------------------------------

        customer = get_customer_by_id(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found",
            )

        # ----------------------------------------------------
        # Generate AI recommendation
        # ----------------------------------------------------

        ai_message = generate_ai_recommendation(
            customer
        )

        duration = time.perf_counter() - start_time
        logger.info(
            "AI recommendation endpoint completed in %.2fs for customer_id=%s",
            duration,
            customer_id,
        )
        response.headers["X-AI-Duration"] = f"{duration:.2f}s"

        # ----------------------------------------------------
        # Safely read customer values
        # ----------------------------------------------------

        if isinstance(customer, dict):

            customer_id_value = customer.get(
                "customer_id"
            )

            segment = customer.get(
                "segment"
            )

            campaign = customer.get(
                "campaign"
            )

            priority = customer.get(
                "priority"
            )

            marketing_strategy = customer.get(
                "marketing_strategy"
            )

            recommended_action = customer.get(
                "recommended_action"
            )

        else:

            customer_id_value = getattr(
                customer,
                "customer_id",
                None,
            )

            segment = getattr(
                customer,
                "segment",
                None,
            )

            campaign = getattr(
                customer,
                "campaign",
                None,
            )

            priority = getattr(
                customer,
                "priority",
                None,
            )

            marketing_strategy = getattr(
                customer,
                "marketing_strategy",
                None,
            )

            recommended_action = getattr(
                customer,
                "recommended_action",
                None,
            )

        # ----------------------------------------------------
        # Auto-save analysis history to database
        # ----------------------------------------------------
        try:
            cust_payload = customer if isinstance(customer, dict) else (
                {c.name: getattr(customer, c.name) for c in customer.__table__.columns}
                if hasattr(customer, "__table__") else {}
            )
            record_analysis_history(
                db=db,
                user=current_user,
                customer_id=customer_id_value or customer_id,
                customer_data=cust_payload,
                ai_message=ai_message,
                marketing_strategy=marketing_strategy,
                recommended_action=recommended_action,
            )
        except Exception as save_err:
            logger.warning(f"Could not auto-save analysis history: {save_err}")

        # ----------------------------------------------------
        # Return AI response
        # ----------------------------------------------------

        return {
            "customer_id": customer_id_value,
            "segment": segment,
            "campaign": campaign,
            "priority": priority,
            "marketing_strategy": marketing_strategy,
            "recommended_action": recommended_action,
            "ai_message": ai_message,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "Error generating AI recommendation for customer %s: %s",
            customer_id,
            exc,
        )
        # Attempt graceful fallback if customer was located
        if "customer" in locals() and customer:
            from app.services.ai_service import _generate_smart_fallback
            seg = customer.get("segment") if isinstance(customer, dict) else getattr(customer, "segment", "Valued Customer")
            act = customer.get("recommended_action") if isinstance(customer, dict) else getattr(customer, "recommended_action", "")
            strat = customer.get("marketing_strategy") if isinstance(customer, dict) else getattr(customer, "marketing_strategy", "")
            fallback_msg = _generate_smart_fallback(str(seg), str(act), str(strat))
            return {
                "customer_id": customer.get("customer_id") if isinstance(customer, dict) else getattr(customer, "customer_id", customer_id),
                "segment": seg,
                "campaign": customer.get("campaign") if isinstance(customer, dict) else getattr(customer, "campaign", "Personalized Campaign"),
                "priority": customer.get("priority") if isinstance(customer, dict) else getattr(customer, "priority", "Medium"),
                "marketing_strategy": strat or "Deliver personalized engagement",
                "recommended_action": act or "Engage with personalized recommendations",
                "ai_message": fallback_msg,
            }

        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate AI recommendation: {str(exc)}",
        )


# ============================================================
# EXPORT CUSTOMERS REPORT (MULTI-FORMAT: CSV, XLSX, PDF, DOCX, JSON)
# ============================================================

def _get_filtered_export_customers(
    segment: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
) -> List[dict]:
    """
    Retrieve and filter customers based on active segment, priority, and search filters.
    """
    if segment and segment.strip():
        customers = get_customers_by_segment(segment.strip())
    elif search and search.strip():
        customers = search_customers(search.strip())
    else:
        customers = get_all_customers()

    if priority and priority.strip():
        priority_clean = priority.strip().lower()
        customers = [
            c for c in customers
            if str(c.get("priority", "")).strip().lower() == priority_clean
        ]

    # If search was provided together with segment, apply search filter as well
    if segment and segment.strip() and search and search.strip():
        s = search.strip().lower()
        customers = [
            c for c in customers
            if s in str(c.get("customer_id", "")).lower()
            or s in str(c.get("segment", "")).lower()
            or s in str(c.get("campaign", "")).lower()
            or s in str(c.get("priority", "")).lower()
        ]

    return customers


def _build_customer_export_response(
    file_format: str,
    customers: List[dict],
    filter_info: dict,
) -> Response:
    """
    Generate the report file in the requested format and wrap in a FastAPI Response.
    """
    fmt = file_format.lower().strip().lstrip(".")

    if fmt == "csv":
        content, filename = generate_csv_report(customers, filter_info)
        media_type = "text/csv; charset=utf-8"
        body = content.encode("utf-8") if isinstance(content, str) else content

    elif fmt in ("xlsx", "excel"):
        body, filename = generate_excel_report(customers, filter_info)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif fmt == "pdf":
        body, filename = generate_pdf_report(customers, filter_info)
        media_type = "application/pdf"

    elif fmt in ("docx", "word"):
        body, filename = generate_docx_report(customers, filter_info)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif fmt == "json":
        content, filename = generate_json_report(customers, filter_info)
        media_type = "application/json; charset=utf-8"
        body = content.encode("utf-8") if isinstance(content, str) else content

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format '{file_format}'. Supported formats are: csv, xlsx, pdf, docx, json.",
        )

    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/export/csv",
    summary="Export customers report to CSV",
)
def export_customers_csv(
    segment: Optional[str] = Query(None, description="Filter by customer segment (e.g. Champions, At Risk)"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g. High, Medium, Low)"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Generate a downloadable CSV report for customers.
    Preserves exact backward-compatibility for existing CSV downloads.
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response("csv", customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers CSV: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export customer report: {str(exc)}",
        )


@router.get(
    "/export/xlsx",
    summary="Export customers report to Excel (.xlsx)",
)
@router.get(
    "/export/excel",
    include_in_schema=False,
)
def export_customers_xlsx(
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Generate a formatted Excel (.xlsx) report for customers.
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response("xlsx", customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers XLSX: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export Excel report: {str(exc)}",
        )


@router.get(
    "/export/pdf",
    summary="Export customers report to PDF (.pdf)",
)
def export_customers_pdf(
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Generate a styled landscape PDF report for customers.
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response("pdf", customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers PDF: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export PDF report: {str(exc)}",
        )


@router.get(
    "/export/docx",
    summary="Export customers report to Word (.docx)",
)
@router.get(
    "/export/word",
    include_in_schema=False,
)
def export_customers_docx(
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Generate a professional Microsoft Word document (.docx) report for customers.
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response("docx", customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers DOCX: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export Word report: {str(exc)}",
        )


@router.get(
    "/export/json",
    summary="Export customers report to JSON (.json)",
)
def export_customers_json(
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Generate structured, pretty-printed JSON report for customers.
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response("json", customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers JSON: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export JSON report: {str(exc)}",
        )


@router.get(
    "/export/{file_format}",
    summary="Export customers report in specified format",
)
def export_customers_by_format(
    file_format: str,
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search query"),
):
    """
    Unified endpoint to export customers in any supported format (csv, xlsx, pdf, docx, json).
    """
    try:
        customers = _get_filtered_export_customers(segment, priority, search)
        filter_info = {"segment": segment, "priority": priority, "search": search}
        return _build_customer_export_response(file_format, customers, filter_info)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error exporting customers {file_format}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export report as {file_format}: {str(exc)}",
        )


# ============================================================
# EXPORT SEGMENTS SUMMARY REPORT (CSV)
# ============================================================

@router.get(
    "/export/segments-summary/csv",
    summary="Export segment summary metrics to CSV",
)
def export_segments_summary_csv():
    """
    Generate a downloadable CSV report summarizing customer segments.
    """
    try:
        summaries = get_segment_summary()
        total_customers = sum(s.get("customer_count", 0) for s in summaries)
        total_revenue = sum(s.get("total_revenue", 0) for s in summaries)

        output = io.StringIO()
        fieldnames = [
            "Segment",
            "Customer_Count",
            "Customer_Percentage",
            "Avg_Recency",
            "Avg_Frequency",
            "Avg_Monetary",
            "Total_Revenue",
            "Revenue_Percentage",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for s in summaries:
            count = s.get("customer_count", 0)
            rev = s.get("total_revenue", 0.0)
            count_pct = f"{(count / total_customers * 100):.1f}%" if total_customers > 0 else "0.0%"
            rev_pct = f"{(rev / total_revenue * 100):.1f}%" if total_revenue > 0 else "0.0%"

            writer.writerow({
                "Segment": s.get("segment", ""),
                "Customer_Count": count,
                "Customer_Percentage": count_pct,
                "Avg_Recency": s.get("avg_recency", ""),
                "Avg_Frequency": s.get("avg_frequency", ""),
                "Avg_Monetary": f"{s.get('avg_monetary', 0):.2f}",
                "Total_Revenue": f"{rev:.2f}",
                "Revenue_Percentage": rev_pct,
            })

        csv_content = output.getvalue()
        output.close()

        filename = "customer_segments_summary_report.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as exc:
        logger.error(f"Error exporting segment summary CSV: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to export segment summary: {str(exc)}",
        )