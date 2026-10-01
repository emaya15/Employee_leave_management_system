# app/auth/dependencies.py
# Reusable FastAPI dependencies for "who is logged in?" and "are they allowed?".
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

# tokenUrl makes the "Authorize" button in Swagger call POST /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# Same thing, but does not fail when no token is sent (used by /auth/register)
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _user_from_token(token: str, db: Session) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    return _user_from_token(token, db)


def get_optional_user(
    token: str = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)
):
    """Returns the logged-in user, or None if no token was sent."""
    if token is None:
        return None
    return _user_from_token(token, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_hr_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.HR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="HR or Admin access required"
        )
    return current_user
