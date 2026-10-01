# app/services/leave_service.py
# ALL leave business rules live in this file (not in the router).
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
from app.models.user import User, UserRole
from app.schemas.leave import LeaveCreate, LeaveReject
from app.services.employee_service import check_employee_access, get_employee_or_404

# Yearly leave balance for every employee
YEARLY_LEAVE_ALLOCATION = {
    LeaveType.SICK: 12,
    LeaveType.CASUAL: 10,
    LeaveType.EARNED: 15,
}


# ---------------------------------------------------------------- helpers
def count_working_days(start: date, end: date) -> int:
    """Count days from start to end (inclusive), skipping Saturday and Sunday."""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday=0 ... Friday=4, Saturday=5, Sunday=6
            days += 1
        current += timedelta(days=1)
    return days


def _days_by_status(db: Session, employee_id: int, leave_type: LeaveType,
                    leave_status: LeaveStatus, year: int) -> int:
    """Total days of one leave type + status in a given year."""
    total = (
        db.query(func.coalesce(func.sum(LeaveRequest.total_days), 0))
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == leave_status,
            LeaveRequest.start_date >= date(year, 1, 1),
            LeaveRequest.start_date <= date(year, 12, 31),
        )
        .scalar()
    )
    return int(total or 0)


def _get_leave_or_404(db: Session, leave_id: int) -> LeaveRequest:
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if leave is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    return leave


def _require_pending(leave: LeaveRequest) -> None:
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only Pending leaves can be changed (this leave is {leave.status.value})",
        )


# ---------------------------------------------------------------- balance
def calculate_leave_balance(db: Session, employee_id: int, year: int) -> dict:
    get_employee_or_404(db, employee_id)
    balances = []
    for leave_type, allocated in YEARLY_LEAVE_ALLOCATION.items():
        used = _days_by_status(db, employee_id, leave_type, LeaveStatus.APPROVED, year)
        pending = _days_by_status(db, employee_id, leave_type, LeaveStatus.PENDING, year)
        balances.append({
            "leave_type": leave_type,
            "allocated": allocated,
            "used": used,                 # balance is deducted only for approved leaves
            "pending": pending,
            "available": allocated - used,
        })
    return {"employee_id": employee_id, "year": year, "balances": balances}


def get_employee_leave_balance(db: Session, current_user: User, employee_id: int, year: int) -> dict:
    get_employee_or_404(db, employee_id)
    check_employee_access(current_user, employee_id)
    return calculate_leave_balance(db, employee_id, year)


# ---------------------------------------------------------------- apply
def apply_leave(db: Session, current_user: User, data: LeaveCreate) -> LeaveRequest:
    # Rule 1: employees apply only for themselves (the id comes from the login, not the body)
    if current_user.employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Your account is not linked to an employee profile")
    employee = get_employee_or_404(db, current_user.employee_id)

    # Rule 14: inactive employees cannot apply
    if not employee.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Inactive employees cannot apply for leave")

    # Rule 4: end date cannot be before start date
    if data.end_date < data.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="End date cannot be before start date")

    # Rule 5: no leave in the past
    if data.start_date < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Leave cannot be applied for past dates")

    # Keep things simple: one request must stay inside one calendar year
    if data.start_date.year != data.end_date.year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A leave request must be within a single calendar year")

    # Rules 6 + 7: total days, skipping Saturday and Sunday
    total_days = count_working_days(data.start_date, data.end_date)
    if total_days == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Selected dates contain only weekends; no leave needed")

    # Rule 10: no overlap with another Pending/Approved leave of the same employee
    overlapping = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            LeaveRequest.start_date <= data.end_date,
            LeaveRequest.end_date >= data.start_date,
        )
        .first()
    )
    if overlapping is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Leave request overlaps with an existing leave")

    # Rule 8: enough balance? (Rule 9: only approved leaves are deducted)
    year = data.start_date.year
    used = _days_by_status(db, employee.id, data.leave_type, LeaveStatus.APPROVED, year)
    available = YEARLY_LEAVE_ALLOCATION[data.leave_type] - used
    if total_days > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient {data.leave_type.value} leave balance "
                   f"(requested {total_days}, available {available})",
        )

    leave = LeaveRequest(
        employee_id=employee.id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=total_days,
        reason=data.reason,
        status=LeaveStatus.PENDING,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


# ---------------------------------------------------------------- read
def _filtered_leave_query(db: Session, employee_id, leave_status, leave_type, from_date, to_date):
    query = db.query(LeaveRequest)
    if employee_id is not None:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    if leave_status is not None:
        query = query.filter(LeaveRequest.status == leave_status)
    if leave_type is not None:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    # from_date/to_date: keep leaves that overlap with the given date range
    if from_date is not None:
        query = query.filter(LeaveRequest.end_date >= from_date)
    if to_date is not None:
        query = query.filter(LeaveRequest.start_date <= to_date)
    return query


def list_leaves(
    db: Session, current_user: User, skip: int, limit: int,
    leave_status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    employee_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[LeaveRequest]:
    if current_user.role == UserRole.EMPLOYEE:
        # Employees only ever see their own leaves
        if employee_id is not None and employee_id != current_user.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You can only access your own data")
        if current_user.employee_id is None:
            return []
        employee_id = current_user.employee_id

    query = _filtered_leave_query(db, employee_id, leave_status, leave_type, from_date, to_date)
    return (query.order_by(LeaveRequest.start_date.desc(), LeaveRequest.id.desc())
            .offset(skip).limit(limit).all())


def list_employee_leaves(
    db: Session, current_user: User, employee_id: int, skip: int, limit: int,
    leave_status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[LeaveRequest]:
    get_employee_or_404(db, employee_id)
    check_employee_access(current_user, employee_id)
    query = _filtered_leave_query(db, employee_id, leave_status, leave_type, from_date, to_date)
    return (query.order_by(LeaveRequest.start_date.desc(), LeaveRequest.id.desc())
            .offset(skip).limit(limit).all())


def get_leave(db: Session, current_user: User, leave_id: int) -> LeaveRequest:
    leave = _get_leave_or_404(db, leave_id)
    check_employee_access(current_user, leave.employee_id)
    return leave


# ---------------------------------------------------------------- approve / reject / cancel
def approve_leave(db: Session, current_user: User, leave_id: int) -> LeaveRequest:
    leave = _get_leave_or_404(db, leave_id)
    _require_pending(leave)  # Rule 11

    # Rule 13: HR cannot approve their own leave
    if current_user.role == UserRole.HR and current_user.employee_id == leave.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="HR cannot approve their own leave")

    # Check the balance again - other leaves may have been approved since this was applied
    year = leave.start_date.year
    used = _days_by_status(db, leave.employee_id, leave.leave_type, LeaveStatus.APPROVED, year)
    available = YEARLY_LEAVE_ALLOCATION[leave.leave_type] - used
    if leave.total_days > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient {leave.leave_type.value} leave balance "
                   f"(requested {leave.total_days}, available {available})",
        )

    leave.status = LeaveStatus.APPROVED
    leave.approved_by = current_user.id
    db.commit()
    db.refresh(leave)
    return leave


def reject_leave(db: Session, current_user: User, leave_id: int, data: LeaveReject) -> LeaveRequest:
    leave = _get_leave_or_404(db, leave_id)
    _require_pending(leave)  # Rule 11

    leave.status = LeaveStatus.REJECTED
    leave.rejection_reason = data.rejection_reason  # Rule 12 (required by the schema)
    db.commit()
    db.refresh(leave)
    return leave


def cancel_leave(db: Session, current_user: User, leave_id: int) -> LeaveRequest:
    leave = _get_leave_or_404(db, leave_id)

    # Rule 2: employees can cancel only their own leaves (Admin can cancel any)
    is_owner = current_user.employee_id is not None and current_user.employee_id == leave.employee_id
    if not is_owner and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can cancel only your own leave")

    _require_pending(leave)  # Rule 11

    leave.status = LeaveStatus.CANCELLED
    db.commit()
    db.refresh(leave)
    return leave
