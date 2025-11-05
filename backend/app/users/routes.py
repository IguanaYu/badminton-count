from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.utils import get_password_hash
from ..dependencies import get_current_user, require_admin
from ..db import get_db
from ..models import User
from ..stats.services import compute_player_summary
from .schemas import UserCreate, UserDetail, UserListResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=UserListResponse)
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).order_by(User.full_name.asc()).all()
    return UserListResponse(users=users)


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        gender=user_in.gender,
        hashed_password=get_password_hash(user_in.password),
        is_admin=user_in.is_admin,
        can_record=user_in.can_record,
        created_by_id=current_user.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.gender is not None:
        user.gender = user_in.gender
    if user_in.can_record is not None:
        user.can_record = user_in.can_record
    if user_in.is_admin is not None:
        user.is_admin = user_in.is_admin
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/details")
def get_user_details(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    summary = compute_player_summary(db, user)
    detail = UserDetail(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        gender=user.gender,
        created_at=user.created_at,
        is_admin=user.is_admin,
        is_root=user.is_root,
        can_record=user.can_record,
        total_matches=summary["total_matches"],
        wins=summary["wins"],
        losses=summary["losses"],
        win_rate=summary["win_rate"],
        singles=summary["singles"],
        doubles=summary["doubles"],
        one_vs_two_as_one=summary["one_vs_two_as_one"],
        one_vs_two_as_two=summary["one_vs_two_as_two"],
        teammates=summary["teammates"],
        calendar=summary["calendar"],
    )
    return detail
