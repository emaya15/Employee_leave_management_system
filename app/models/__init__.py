# app/models/__init__.py
# Importing every model here makes sure SQLAlchemy (and Alembic) know about all tables.
from app.models.department import Department
from app.models.employee import Employee, EmploymentType
from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
from app.models.user import User, UserRole

__all__ = [
    "Department", "Employee", "EmploymentType",
    "LeaveRequest", "LeaveStatus", "LeaveType", "User", "UserRole",
]
