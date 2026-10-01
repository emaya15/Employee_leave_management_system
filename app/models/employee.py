# app/models/employee.py
import enum

from sqlalchemy import (
    Boolean, Column, Date, Enum, ForeignKey, Integer, Numeric, String,
)
from sqlalchemy.orm import relationship

from app.database import Base, TimestampMixin


class EmploymentType(str, enum.Enum):
    FULL_TIME = "Full-Time"
    PART_TIME = "Part-Time"
    INTERN = "Intern"
    CONTRACT = "Contract"


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(10), nullable=False)
    # RESTRICT = the database refuses to delete a department that still has employees
    department_id = Column(
        Integer, ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    designation = Column(String(100), nullable=False)
    salary = Column(Numeric(10, 2), nullable=False)
    date_of_joining = Column(Date, nullable=False)
    employment_type = Column(
        # values_callable makes MySQL store "Full-Time" instead of "FULL_TIME"
        Enum(EmploymentType, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # One employee belongs to one department
    department = relationship("Department", back_populates="employees")
    # One employee has many leave requests
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    # A login account (User) can be linked to an employee profile
    user = relationship("User", back_populates="employee", uselist=False)
