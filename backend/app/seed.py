from sqlalchemy.orm import Session

from .auth.utils import get_password_hash
from .models import Gender, User


DEFAULT_ADMIN = {
    "username": "admin",
    "full_name": "Admin",
    "gender": Gender.other,
    "password": "admin123",
    "is_admin": True,
    "is_root": True,
    "can_record": True,
}


def ensure_admin_user(db: Session) -> User:
    admin = db.query(User).filter(User.username == DEFAULT_ADMIN["username"]).first()
    if admin:
        return admin

    admin = User(
        username=DEFAULT_ADMIN["username"],
        full_name=DEFAULT_ADMIN["full_name"],
        gender=DEFAULT_ADMIN["gender"],
        hashed_password=get_password_hash(DEFAULT_ADMIN["password"]),
        is_admin=DEFAULT_ADMIN["is_admin"],
        is_root=DEFAULT_ADMIN["is_root"],
        can_record=DEFAULT_ADMIN["can_record"],
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def seed_data(db: Session):
    ensure_admin_user(db)
