# app/models/user.py
import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    HR = "HR"
    EMPLOYEE = "Employee"


class User(TimestampMixin, Base):
    """A login account. It may be linked to an employee profile."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=UserRole.EMPLOYEE,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    # unique=True -> one employee profile can belong to only one login account
    # SET NULL     -> if the employee row were ever removed, the user just loses the link
    employee_id = Column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL"),
        unique=True, nullable=True,
    )

    employee = relationship("Employee", back_populates="user")
