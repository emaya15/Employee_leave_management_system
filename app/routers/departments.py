# app/routers/departments.py
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin, require_hr_or_admin
from app.database import get_db
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.schemas.employee import EmployeeResponse
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)):
    return department_service.create_department(db, data)


@router.get("", response_model=List[DepartmentResponse])
def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return department_service.list_departments(db, skip, limit, is_active)


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return department_service.get_department_or_404(db, department_id)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, data: DepartmentUpdate,
                      db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return department_service.update_department(db, department_id, data)


@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)):
    department_service.delete_department(db, department_id)
    return {"detail": "Department deleted successfully"}


@router.get("/{department_id}/employees", response_model=List[EmployeeResponse])
def list_department_employees(
    department_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_hr_or_admin),
):
    return department_service.list_department_employees(db, department_id, skip, limit, is_active)
