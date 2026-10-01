# app/models/department.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base, TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, nullable=False)
    location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # One department has many employees
    employees = relationship("Employee", back_populates="department")
