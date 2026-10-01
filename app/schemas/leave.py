# app/schemas/leave.py
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.leave import LeaveStatus, LeaveType


class LeaveCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=255)


class LeaveReject(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    rejection_reason: str = Field(min_length=3, max_length=255)


class LeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: LeaveStatus
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LeaveBalanceItem(BaseModel):
    leave_type: LeaveType
    allocated: int
    used: int       # approved days only
    pending: int    # days waiting for approval (not deducted yet)
    available: int  # allocated - used


class LeaveBalanceResponse(BaseModel):
    employee_id: int
    year: int
    balances: List[LeaveBalanceItem]
