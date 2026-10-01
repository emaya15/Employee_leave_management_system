# app/services/auth_service.py
# Business logic for registering and logging in.
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


def register_user(db: Session, data: RegisterRequest, current_user: Optional[User]) -> User:
    email = data.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists")

    role = data.role
    if db.query(User).count() == 0:
        # Very first account in an empty system becomes the Admin (bootstrap).
        role = UserRole.ADMIN
    elif role != UserRole.EMPLOYEE:
        # After that, only a logged-in Admin can create Admin or HR accounts.
        if current_user is None or current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Only an Admin can create Admin or HR accounts")

    # If an employee profile with the same email exists, link the account to it.
    employee = db.query(Employee).filter(Employee.email == email).first()
    employee_id = None
    if employee is not None and employee.user is None:
        employee_id = employee.id

    user = User(
        full_name=data.full_name,
        email=email,
        hashed_password=hash_password(data.password),
        role=role,
        employee_id=employee_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists")
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User is inactive and cannot log in")
    return create_access_token(user.id)
