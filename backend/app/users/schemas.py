from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..models import Gender


class UserBase(BaseModel):
    username: str
    full_name: str
    gender: Gender
    can_record: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    is_admin: bool = False


class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_root: bool
    created_at: datetime

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    users: List[UserResponse]


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    can_record: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserDetail(UserResponse):
    total_matches: int
    wins: int
    losses: int
    win_rate: float
    singles: dict
    doubles: dict
    one_vs_two_as_one: dict
    one_vs_two_as_two: dict
    teammates: list
    calendar: list
