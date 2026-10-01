# app/schemas/department.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    department_name: str = Field(min_length=2, max_length=100)
    location: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    """All fields optional: send only what you want to change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    department_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    location: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_name: str
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
