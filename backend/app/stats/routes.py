from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_current_user
from ..db import get_db
from ..models import User
from .services import compute_player_summary, compute_rankings

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/rankings")
def get_rankings(db: Session = Depends(get_db)):
    rankings = compute_rankings(db)
    return [
        {
            "user_id": item["user"].id,
            "full_name": item["user"].full_name,
            "win_rate": item["win_rate"],
            "wins": item["wins"],
            "losses": item["losses"],
            "total_matches": item["total_matches"],
        }
        for item in rankings
    ]


@router.get("/players/me")
def get_me_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    summary = compute_player_summary(db, current_user)
    return _format_summary(summary)


@router.get("/players/{user_id}")
def get_player_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    summary = compute_player_summary(db, user)
    return _format_summary(summary)


def _format_summary(summary):
    user = summary["user"]
    return {
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "gender": user.gender,
        },
        "total_matches": summary["total_matches"],
        "wins": summary["wins"],
        "losses": summary["losses"],
        "win_rate": summary["win_rate"],
        "singles": summary["singles"],
        "doubles": summary["doubles"],
        "one_vs_two_as_one": summary["one_vs_two_as_one"],
        "one_vs_two_as_two": summary["one_vs_two_as_two"],
        "teammates": summary["teammates"],
        "calendar": summary["calendar"],
    }
