import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class MatchType(str, enum.Enum):
    singles = "singles"
    doubles = "doubles"
    one_vs_two = "one_vs_two"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_root = Column(Boolean, default=False)
    can_record = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_users = relationship("User", backref="creator", remote_side=[id])
    recorded_matches = relationship("Match", back_populates="recorded_by")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    played_at = Column(DateTime, nullable=False, index=True)
    session_number = Column(Integer, nullable=True)
    match_type = Column(Enum(MatchType), nullable=False)
    score_a = Column(Integer, nullable=False)
    score_b = Column(Integer, nullable=False)
    winner_side = Column(String(1), nullable=False)
    notes = Column(String(255), nullable=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    recorded_by = relationship("User", back_populates="recorded_matches")
    participants = relationship("MatchParticipant", back_populates="match", cascade="all, delete-orphan")


class MatchParticipant(Base):
    __tablename__ = "match_participants"
    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_user"),
        UniqueConstraint("match_id", "side", "slot", name="uq_match_side_slot"),
    )

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    side = Column(String(1), nullable=False)  # "A" or "B"
    slot = Column(Integer, nullable=False)  # 1 or 2

    match = relationship("Match", back_populates="participants")
    user = relationship("User")


def resolve_winner(score_a: int, score_b: int) -> str:
    if score_a == score_b:
        raise ValueError("Scores cannot be tied in badminton matches.")
    return "A" if score_a > score_b else "B"


def expected_slots(match_type: MatchType) -> tuple[int, int]:
    if match_type == MatchType.singles:
        return (1, 1)
    if match_type == MatchType.doubles:
        return (2, 2)
    if match_type == MatchType.one_vs_two:
        return (1, 2)
    raise ValueError("Unsupported match type")
