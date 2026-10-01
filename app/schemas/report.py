# app/schemas/report.py
from typing import List

from pydantic import BaseModel

from app.models.leave import LeaveStatus, LeaveType


class DepartmentCount(BaseModel):
    department_id: int
    department_name: str
    employee_count: int  # active employees only


class DashboardResponse(BaseModel):
    total_employees: int
    active_employees: int
    employees_per_department: List[DepartmentCount]
    pending_leave_requests: int
    employees_on_leave_today: int


class LeaveSummaryItem(BaseModel):
    leave_type: LeaveType
    status: LeaveStatus
    request_count: int
    total_days: int


class LeaveSummaryResponse(BaseModel):
    month: int
    year: int
    summary: List[LeaveSummaryItem]
