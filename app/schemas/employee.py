# app/schemas/employee.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.employee import EmploymentType

PHONE_PATTERN = r"^[0-9]{10}$"  # exactly 10 digits


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    employee_code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(pattern=PHONE_PATTERN, description="Exactly 10 digits")
    department_id: int
    designation: str = Field(min_length=2, max_length=100)
    salary: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    date_of_joining: date
    employment_type: EmploymentType
    is_active: bool = True

    @field_validator("date_of_joining")
    @classmethod
    def joining_date_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date of joining cannot be in the future")
        return value


class EmployeeUpdate(BaseModel):
    """All fields optional: send only what you want to change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    employee_code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    department_id: Optional[int] = None
    designation: Optional[str] = Field(default=None, min_length=2, max_length=100)
    salary: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    date_of_joining: Optional[date] = None
    employment_type: Optional[EmploymentType] = None
    is_active: Optional[bool] = None

    @field_validator("date_of_joining")
    @classmethod
    def joining_date_not_in_future(cls, value):
        if value is not None and value > date.today():
            raise ValueError("Date of joining cannot be in the future")
        return value


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    name: str
    email: EmailStr
    phone: str
    department_id: int
    designation: str
    salary: Decimal
    date_of_joining: date
    employment_type: EmploymentType
    is_active: bool
    created_at: datetime
    updated_at: datetime
