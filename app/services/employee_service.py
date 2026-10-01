# app/services/employee_service.py
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee, EmploymentType
from app.models.user import User, UserRole
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

# Columns that clients are allowed to sort by
SORT_COLUMNS = {
    "name": Employee.name,
    "salary": Employee.salary,
    "date_of_joining": Employee.date_of_joining,
    "employee_code": Employee.employee_code,
    "created_at": Employee.created_at,
}


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


def check_employee_access(current_user: User, employee_id: int) -> None:
    """Admin/HR can see any employee. A normal Employee can only see themselves."""
    if current_user.role == UserRole.EMPLOYEE and current_user.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only access your own data")


def _check_unique(db: Session, employee_code: Optional[str], email: Optional[str],
                  exclude_id: Optional[int] = None) -> None:
    if employee_code is not None:
        query = db.query(Employee).filter(Employee.employee_code == employee_code)
        if exclude_id is not None:
            query = query.filter(Employee.id != exclude_id)
        if query.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Employee with this employee code already exists")
    if email is not None:
        query = db.query(Employee).filter(Employee.email == email)
        if exclude_id is not None:
            query = query.filter(Employee.id != exclude_id)
        if query.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Employee with this email already exists")


def _check_department(db: Session, department_id: int) -> None:
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if not department.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Department is not active")


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    values = data.model_dump()
    values["email"] = values["email"].lower()

    _check_unique(db, values["employee_code"], values["email"])
    _check_department(db, values["department_id"])

    employee = Employee(**values)
    db.add(employee)
    try:
        db.flush()  # gives the employee an id without saving permanently yet

        # If this person already has a login account (same email), link them.
        user = db.query(User).filter(
            User.email == employee.email, User.employee_id.is_(None)
        ).first()
        if user is not None:
            user.employee_id = employee.id

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Employee code or email already exists")
    db.refresh(employee)
    return employee


def list_employees(
    db: Session, skip: int, limit: int,
    name: Optional[str] = None,
    department_id: Optional[int] = None,
    designation: Optional[str] = None,
    employment_type: Optional[EmploymentType] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "id",
    order: str = "asc",
) -> List[Employee]:
    query = db.query(Employee)

    # All filtering happens in the SQL query, not in Python
    if name:
        query = query.filter(Employee.name.ilike(f"%{name}%"))  # partial match
    if department_id is not None:
        query = query.filter(Employee.department_id == department_id)
    if designation:
        query = query.filter(Employee.designation.ilike(f"%{designation}%"))
    if employment_type is not None:
        query = query.filter(Employee.employment_type == employment_type)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)

    sort_column = SORT_COLUMNS.get(sort_by, Employee.id)
    sort_column = sort_column.desc() if order == "desc" else sort_column.asc()
    # Employee.id as a tie-breaker keeps pages stable
    return query.order_by(sort_column, Employee.id).offset(skip).limit(limit).all()


def update_employee(db: Session, employee_id: int, data: EmployeeUpdate) -> Employee:
    employee = get_employee_or_404(db, employee_id)
    changes = data.model_dump(exclude_unset=True)

    # These columns can never be NULL, so ignore explicit nulls for them
    changes = {key: value for key, value in changes.items() if value is not None}

    if "email" in changes:
        changes["email"] = changes["email"].lower()

    _check_unique(db, changes.get("employee_code"), changes.get("email"),
                  exclude_id=employee_id)
    if "department_id" in changes:
        _check_department(db, changes["department_id"])

    for field, value in changes.items():
        setattr(employee, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Employee code or email already exists")
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee_id: int) -> None:
    """Soft delete: the row stays in the database, we only mark it inactive."""
    employee = get_employee_or_404(db, employee_id)
    employee.is_active = False
    db.commit()
