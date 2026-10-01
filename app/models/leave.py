# app/models/leave.py
import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base, TimestampMixin


class LeaveType(str, enum.Enum):
    SICK = "Sick"
    CASUAL = "Casual"
    EARNED = "Earned"


class LeaveStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class LeaveRequest(TimestampMixin, Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    leave_type = Column(
        Enum(LeaveType, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(
        Enum(LeaveStatus, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=LeaveStatus.PENDING,
        index=True,
    )
    # The user (Admin/HR) who approved the leave
    approved_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason = Column(String(255), nullable=True)

    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])
