# ============================================================
# ANALYSIS HISTORY ROUTER
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.schemas import (
    AnalysisHistoryPaginationResponse,
    AnalysisHistoryDetailResponse,
)
from app.services.auth_service import get_current_user
from app.services.history_service import (
    get_history_records,
    get_history_by_id,
    delete_history_record,
    generate_historical_report,
)

logger = logging.getLogger("history_router")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/history",
    tags=["Analysis History"],
)


# ============================================================
# GET PAGINATED ANALYSIS HISTORY RECORDS
# ============================================================

@router.get(
    "",
    response_model=AnalysisHistoryPaginationResponse,
    summary="Get paginated analysis history records",
)
def list_analysis_history(
    search: Optional[str] = Query(None, description="Search by Customer ID, Name, or Analysis ID"),
    segment: Optional[str] = Query(None, description="Filter by customer segment (e.g. Champions, At Risk)"),
    start_date: Optional[str] = Query(None, description="Filter records on or after YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter records on or before YYYY-MM-DD"),
    recommendation_type: Optional[str] = Query(None, description="Search within AI recommendation keywords or actions"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve analysis history with search, filters, pagination, and role-based access.
    - Admins see all users' analysis records.
    - Analysts and registered users see only their own saved records.
    """
    try:
        data = get_history_records(
            db=db,
            current_user=current_user,
            search=search,
            segment=segment,
            start_date=start_date,
            end_date=end_date,
            recommendation_type=recommendation_type,
            page=page,
            page_size=page_size,
        )
        return data

    except Exception as exc:
        logger.error(f"Error listing analysis history: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve analysis history: {str(exc)}"
        )


# ============================================================
# GET SINGLE HISTORICAL ANALYSIS DETAIL
# ============================================================

@router.get(
    "/{history_id}",
    response_model=AnalysisHistoryDetailResponse,
    summary="Get detailed historical analysis by ID",
)
def get_analysis_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve complete historical analysis snapshot including customer attributes,
    RFM metrics, segmentation result, and stored AI recommendation.
    Guarantees that previously saved AI recommendation is returned without calling AI again.
    """
    try:
        record = get_history_by_id(
            db=db,
            history_id=history_id,
            current_user=current_user,
        )
        return record

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Error retrieving analysis #{history_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve analysis detail: {str(exc)}"
        )


# ============================================================
# DELETE HISTORICAL ANALYSIS RECORD
# ============================================================

@router.delete(
    "/{history_id}",
    summary="Delete historical analysis record",
)
def delete_analysis(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis record with role authorization check and audit logging.
    - Admins can delete any record.
    - Analysts/Users can only delete their own records.
    """
    try:
        delete_history_record(
            db=db,
            history_id=history_id,
            current_user=current_user,
        )
        return {
            "success": True,
            "message": f"Analysis history record #{history_id} deleted successfully."
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Error deleting analysis #{history_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to delete analysis record: {str(exc)}"
        )


# ============================================================
# DOWNLOAD HISTORICAL REPORT (CSV, XLSX, PDF, DOCX, JSON)
# ============================================================

@router.get(
    "/{history_id}/export/{file_format}",
    summary="Download historical analysis report in selected format",
)
def export_historical_report(
    history_id: int,
    file_format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download the historical analysis report in CSV, XLSX, PDF, DOCX, or JSON format.
    Guarantees the exported file contains the saved historical snapshot data.
    """
    try:
        body, filename, media_type = generate_historical_report(
            db=db,
            history_id=history_id,
            file_format=file_format,
            current_user=current_user,
        )

        return Response(
            content=body,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Error exporting historical report #{history_id} as {file_format}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to export historical report: {str(exc)}"
        )
