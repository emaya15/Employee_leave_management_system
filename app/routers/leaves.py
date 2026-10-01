# app/routers/leaves.py
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_hr_or_admin
from app.database import get_db
from app.models.leave import LeaveStatus, LeaveType
from app.models.user import User
from app.schemas.leave import LeaveBalanceResponse, LeaveCreate, LeaveReject, LeaveResponse
from app.services import leave_service

router = APIRouter(prefix="/leaves", tags=["Leaves"])
# Routes that start with /employees/{id}/... but belong to leave management
employee_leaves_router = APIRouter(prefix="/employees", tags=["Leaves"])


@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(data: LeaveCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return leave_service.apply_leave(db, current_user, data)


@router.get("", response_model=List[LeaveResponse])
def list_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[LeaveStatus] = Query(None, alias="status"),
    leave_type: Optional[LeaveType] = None,
    employee_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return leave_service.list_leaves(db, current_user, skip, limit, status_filter,
                                     leave_type, employee_id, from_date, to_date)


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(leave_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return leave_service.get_leave(db, current_user, leave_id)


@router.put("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(leave_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_hr_or_admin)):
    return leave_service.approve_leave(db, user, leave_id)


@router.put("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(leave_id: int, data: LeaveReject, db: Session = Depends(get_db),
                 user: User = Depends(require_hr_or_admin)):
    return leave_service.reject_leave(db, user, leave_id, data)


@router.put("/{leave_id}/cancel", response_model=LeaveResponse)
def cancel_leave(leave_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return leave_service.cancel_leave(db, current_user, leave_id)


@employee_leaves_router.get("/{employee_id}/leaves", response_model=List[LeaveResponse])
def list_employee_leaves(
    employee_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[LeaveStatus] = Query(None, alias="status"),
    leave_type: Optional[LeaveType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return leave_service.list_employee_leaves(db, current_user, employee_id, skip, limit,
                                              status_filter, leave_type, from_date, to_date)


@employee_leaves_router.get("/{employee_id}/leave-balance", response_model=LeaveBalanceResponse)
def get_leave_balance(
    employee_id: int,
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Defaults to the current year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return leave_service.get_employee_leave_balance(
        db, current_user, employee_id, year or date.today().year
    )
