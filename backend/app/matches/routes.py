from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, require_record_permission
from ..db import get_db
from ..models import Match, MatchParticipant, MatchType, User, expected_slots, resolve_winner
from .schemas import MatchCreate, MatchListResponse, MatchParticipantResponse, MatchResponse

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/", response_model=MatchListResponse)
def list_matches(
    only_mine: bool = Query(False, description="Only show matches the current user participated in"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Match).order_by(Match.played_at.desc())
    if only_mine:
        query = query.join(MatchParticipant).filter(MatchParticipant.user_id == current_user.id)
    matches = query.all()
    return MatchListResponse(matches=[_to_response(match) for match in matches])


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _to_response(match)


@router.post("/", response_model=MatchResponse)
def create_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_record_permission),
):
    expected_a, expected_b = expected_slots(match_in.match_type)
    if len(match_in.side_a_players) != expected_a or len(match_in.side_b_players) != expected_b:
        raise HTTPException(status_code=400, detail="Player counts do not match the match type")

    players = match_in.side_a_players + match_in.side_b_players
    if len(players) != len(set(players)):
        raise HTTPException(status_code=400, detail="Duplicate players in match")

    existing_players = db.query(User.id).filter(User.id.in_(players)).all()
    if len(existing_players) != len(players):
        raise HTTPException(status_code=404, detail="One or more players not found")

    winner_side = resolve_winner(match_in.score_a, match_in.score_b)

    match = Match(
        played_at=match_in.played_at,
        session_number=match_in.session_number,
        match_type=match_in.match_type,
        score_a=match_in.score_a,
        score_b=match_in.score_b,
        winner_side=winner_side,
        notes=match_in.notes,
        recorded_by_id=current_user.id,
    )

    db.add(match)
    db.flush()

    for idx, user_id in enumerate(match_in.side_a_players, start=1):
        participant = MatchParticipant(match_id=match.id, user_id=user_id, side="A", slot=idx)
        db.add(participant)
    for idx, user_id in enumerate(match_in.side_b_players, start=1):
        participant = MatchParticipant(match_id=match.id, user_id=user_id, side="B", slot=idx)
        db.add(participant)

    db.commit()
    db.refresh(match)
    return _to_response(match)


def _to_response(match: Match) -> MatchResponse:
    participants = [
        MatchParticipantResponse(
            user_id=participant.user.id,
            full_name=participant.user.full_name,
            side=participant.side,
            slot=participant.slot,
        )
        for participant in sorted(match.participants, key=lambda p: (p.side, p.slot))
    ]
    return MatchResponse(
        id=match.id,
        played_at=match.played_at,
        session_number=match.session_number,
        match_type=match.match_type,
        score_a=match.score_a,
        score_b=match.score_b,
        winner_side=match.winner_side,
        notes=match.notes,
        recorded_by=match.recorded_by.full_name,
        participants=participants,
    )
