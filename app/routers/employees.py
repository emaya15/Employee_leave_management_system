# app/routers/employees.py
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_hr_or_admin
from app.database import get_db
from app.models.employee import EmploymentType
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_hr_or_admin)):
    return employee_service.create_employee(db, data)


@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, description="Partial match, e.g. 'rav'"),
    department_id: Optional[int] = None,
    designation: Optional[str] = None,
    employment_type: Optional[EmploymentType] = None,
    is_active: Optional[bool] = None,
    sort_by: Literal["id", "name", "salary", "date_of_joining", "employee_code", "created_at"] = "id",
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    user: User = Depends(require_hr_or_admin),
):
    return employee_service.list_employees(
        db, skip, limit, name, department_id, designation,
        employment_type, is_active, sort_by, order,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    employee = employee_service.get_employee_or_404(db, employee_id)
    employee_service.check_employee_access(current_user, employee_id)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db),
                    user: User = Depends(require_hr_or_admin)):
    return employee_service.update_employee(db, employee_id, data)


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db),
                    user: User = Depends(require_hr_or_admin)):
    employee_service.delete_employee(db, employee_id)  # soft delete
    return {"detail": "Employee deactivated successfully"}
