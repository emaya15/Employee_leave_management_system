# app/routers/reports.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_hr_or_admin
from app.database import get_db
from app.models.user import User
from app.schemas.report import DashboardResponse, LeaveSummaryResponse
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_hr_or_admin)):
    return report_service.get_dashboard(db)


@router.get("/leave-summary", response_model=LeaveSummaryResponse)
def leave_summary(
    month: int = Query(..., ge=1, le=12, description="1 to 12"),
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    user: User = Depends(require_hr_or_admin),
):
    return report_service.get_leave_summary(db, month, year)
