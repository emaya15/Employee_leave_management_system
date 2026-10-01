# app/services/report_service.py
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import and_, distinct, func
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import LeaveRequest, LeaveStatus


def get_dashboard(db: Session) -> dict:
    total_employees = db.query(func.count(Employee.id)).scalar()
    active_employees = (
        db.query(func.count(Employee.id)).filter(Employee.is_active == True).scalar()  # noqa: E712
    )

    # outer join: departments with 0 active employees still appear in the list
    rows = (
        db.query(Department.id, Department.department_name, func.count(Employee.id))
        .outerjoin(
            Employee,
            and_(Employee.department_id == Department.id, Employee.is_active == True),  # noqa: E712
        )
        .group_by(Department.id, Department.department_name)
        .order_by(Department.id)
        .all()
    )
    employees_per_department = [
        {"department_id": dep_id, "department_name": dep_name, "employee_count": count}
        for dep_id, dep_name, count in rows
    ]

    pending_leave_requests = (
        db.query(func.count(LeaveRequest.id))
        .filter(LeaveRequest.status == LeaveStatus.PENDING)
        .scalar()
    )

    today = date.today()
    employees_on_leave_today = (
        db.query(func.count(distinct(LeaveRequest.employee_id)))
        .filter(
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
        )
        .scalar()
    )

    return {
        "total_employees": total_employees or 0,
        "active_employees": active_employees or 0,
        "employees_per_department": employees_per_department,
        "pending_leave_requests": pending_leave_requests or 0,
        "employees_on_leave_today": employees_on_leave_today or 0,
    }


def get_leave_summary(db: Session, month: int, year: int) -> dict:
    if not 1 <= month <= 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Month must be between 1 and 12")

    first_day = date(year, month, 1)
    next_month_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # Leaves that START in the chosen month, grouped by type and status
    rows = (
        db.query(
            LeaveRequest.leave_type,
            LeaveRequest.status,
            func.count(LeaveRequest.id),
            func.coalesce(func.sum(LeaveRequest.total_days), 0),
        )
        .filter(LeaveRequest.start_date >= first_day, LeaveRequest.start_date < next_month_first)
        .group_by(LeaveRequest.leave_type, LeaveRequest.status)
        .all()
    )
    summary = [
        {"leave_type": leave_type, "status": leave_status,
         "request_count": count, "total_days": int(days or 0)}
        for leave_type, leave_status, count, days in rows
    ]
    return {"month": month, "year": year, "summary": summary}
