from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from ..models import MatchType


class MatchCreate(BaseModel):
    played_at: datetime
    session_number: Optional[int] = Field(default=None, ge=1)
    match_type: MatchType
    side_a_players: List[int]
    side_b_players: List[int]
    score_a: int = Field(ge=0)
    score_b: int = Field(ge=0)
    notes: Optional[str] = None

    @validator("side_a_players", "side_b_players")
    def validate_players(cls, v):
        if not v:
            raise ValueError("Players list cannot be empty")
        return v


class MatchParticipantResponse(BaseModel):
    user_id: int
    full_name: str
    side: str
    slot: int


class MatchResponse(BaseModel):
    id: int
    played_at: datetime
    session_number: Optional[int]
    match_type: MatchType
    score_a: int
    score_b: int
    winner_side: str
    notes: Optional[str]
    recorded_by: str
    participants: List[MatchParticipantResponse]

    class Config:
        orm_mode = True


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
