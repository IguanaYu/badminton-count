from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth.utils import decode_access_token
from .db import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")  # type: ignore[assignment]
        if username is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


def require_root(user: User = Depends(get_current_user)) -> User:
    if not user.is_root:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Root privileges required")
    return user


def require_record_permission(user: User = Depends(get_current_user)) -> User:
    if not (user.can_record or user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recording permission required")
    return user
