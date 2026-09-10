from fastapi import APIRouter

from app.schemas import DashboardOverviewResponse
from app.services.customer_services import get_dashboard_overview


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ---------------------------------------------------------
# Dashboard Overview
# ---------------------------------------------------------

@router.get(
    "/overview",
    response_model=DashboardOverviewResponse
)
def dashboard_overview():

    return get_dashboard_overview()