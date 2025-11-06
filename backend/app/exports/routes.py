from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, require_admin, require_root
from ..db import get_db
from ..models import User
from .services import export_all_matches, export_player_matches, export_player_summary

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _to_response(content: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/me/matches")
def export_my_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = export_player_matches(db, current_user)
    return _to_response(content, f"{current_user.username}_matches.xlsx")


@router.get("/me/summary")
def export_my_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = export_player_summary(db, current_user)
    return _to_response(content, f"{current_user.username}_summary.xlsx")


@router.get("/players/{user_id}/matches")
def export_player_matches_admin(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    player = db.query(User).filter(User.id == user_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="User not found")
    content = export_player_matches(db, player)
    return _to_response(content, f"{player.username}_matches.xlsx")


@router.get("/players/{user_id}/summary")
def export_player_summary_admin(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    player = db.query(User).filter(User.id == user_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="User not found")
    content = export_player_summary(db, player)
    return _to_response(content, f"{player.username}_summary.xlsx")


@router.get("/all")
def export_all(current_user: User = Depends(require_root), db: Session = Depends(get_db)):
    content = export_all_matches(db)
    return _to_response(content, "all_matches.xlsx")
