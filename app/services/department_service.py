# app/services/department_service.py
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


def _name_taken(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    query = db.query(Department).filter(Department.department_name == name)
    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)
    return query.first() is not None


def create_department(db: Session, data: DepartmentCreate) -> Department:
    if _name_taken(db, data.department_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Department with this name already exists")
    department = Department(**data.model_dump())
    db.add(department)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Department with this name already exists")
    db.refresh(department)
    return department


def list_departments(db: Session, skip: int, limit: int,
                     is_active: Optional[bool] = None) -> List[Department]:
    query = db.query(Department)
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    return query.order_by(Department.id).offset(skip).limit(limit).all()


def update_department(db: Session, department_id: int, data: DepartmentUpdate) -> Department:
    department = get_department_or_404(db, department_id)
    changes = data.model_dump(exclude_unset=True)  # only the fields the client sent

    new_name = changes.get("department_name")
    if new_name is not None and _name_taken(db, new_name, exclude_id=department_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Department with this name already exists")

    for field, value in changes.items():
        if field in ("department_name", "is_active") and value is None:
            continue  # these two columns cannot be empty
        setattr(department, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Department with this name already exists")
    db.refresh(department)
    return department


def delete_department(db: Session, department_id: int) -> None:
    department = get_department_or_404(db, department_id)

    active_count = db.query(Employee).filter(
        Employee.department_id == department_id, Employee.is_active == True  # noqa: E712
    ).count()
    if active_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Cannot delete department with active employees")

    # Old (inactive) employees still point to this department. The database
    # would block the delete, so we give a clear message instead of a crash.
    if db.query(Employee).filter(Employee.department_id == department_id).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department has inactive employee records; "
                   "set is_active to false instead of deleting it",
        )

    db.delete(department)
    db.commit()


def list_department_employees(db: Session, department_id: int, skip: int, limit: int,
                              is_active: Optional[bool] = None) -> List[Employee]:
    get_department_or_404(db, department_id)  # 404 if the department does not exist
    query = db.query(Employee).filter(Employee.department_id == department_id)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    return query.order_by(Employee.id).offset(skip).limit(limit).all()
