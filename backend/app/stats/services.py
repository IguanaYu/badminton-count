from collections import defaultdict
from datetime import date
from typing import Dict, List, Set

from sqlalchemy.orm import Session

from ..models import Match, MatchParticipant, MatchType, User


def _ratio(wins: int, matches: int) -> float:
    if matches == 0:
        return 0.0
    return round(wins / matches, 4)


def compute_player_summary(db: Session, user: User) -> Dict:
    matches: List[Match] = (
        db.query(Match)
        .join(MatchParticipant)
        .filter(MatchParticipant.user_id == user.id)
        .order_by(Match.played_at.desc())
        .all()
    )

    total_matches = len(matches)
    wins = 0
    category_stats = {
        "singles": {"matches": 0, "wins": 0},
        "doubles": {"matches": 0, "wins": 0},
        "one_vs_two_as_one": {"matches": 0, "wins": 0},
        "one_vs_two_as_two": {"matches": 0, "wins": 0},
    }
    teammate_stats: Dict[int, Dict[str, float]] = defaultdict(lambda: {"matches": 0, "wins": 0, "name": ""})
    calendar_days: Set[date] = set()

    for match in matches:
        calendar_days.add(match.played_at.date())
        participants = match.participants
        user_participant = next(p for p in participants if p.user_id == user.id)
        user_side = user_participant.side
        is_win = match.winner_side == user_side
        if is_win:
            wins += 1

        # Determine teammates and categories
        same_side = [p for p in participants if p.side == user_side]
        teammate_ids = [p.user_id for p in same_side if p.user_id != user.id]

        if match.match_type == MatchType.singles:
            category = "singles"
        elif match.match_type == MatchType.doubles:
            category = "doubles"
        elif match.match_type == MatchType.one_vs_two:
            if len(same_side) == 1:
                category = "one_vs_two_as_one"
            else:
                category = "one_vs_two_as_two"
        else:
            category = "singles"

        category_stats[category]["matches"] += 1
        if is_win:
            category_stats[category]["wins"] += 1

        for teammate_id in teammate_ids:
            teammate_stats[teammate_id]["matches"] += 1
            if is_win:
                teammate_stats[teammate_id]["wins"] += 1

    losses = total_matches - wins

    for values in category_stats.values():
        values["losses"] = values["matches"] - values["wins"]
        values["win_rate"] = _ratio(values["wins"], values["matches"])

    teammate_results = []
    if teammate_stats:
        teammates = db.query(User).filter(User.id.in_(teammate_stats.keys())).all()
        for teammate in teammates:
            stats = teammate_stats[teammate.id]
            teammate_results.append(
                {
                    "user_id": teammate.id,
                    "full_name": teammate.full_name,
                    "matches": stats["matches"],
                    "wins": stats["wins"],
                    "losses": stats["matches"] - stats["wins"],
                    "win_rate": _ratio(stats["wins"], stats["matches"]),
                }
            )

        teammate_results.sort(key=lambda item: (item["win_rate"], item["matches"]), reverse=True)

    return {
        "user": user,
        "total_matches": total_matches,
        "wins": wins,
        "losses": losses,
        "win_rate": _ratio(wins, total_matches),
        "singles": category_stats["singles"],
        "doubles": category_stats["doubles"],
        "one_vs_two_as_one": category_stats["one_vs_two_as_one"],
        "one_vs_two_as_two": category_stats["one_vs_two_as_two"],
        "teammates": teammate_results,
        "calendar": sorted(day.isoformat() for day in calendar_days),
    }


def compute_rankings(db: Session) -> List[Dict]:
    users = db.query(User).all()
    rankings = []
    for user in users:
        summary = compute_player_summary(db, user)
        rankings.append(
            {
                "user": user,
                "win_rate": summary["win_rate"],
                "wins": summary["wins"],
                "losses": summary["losses"],
                "total_matches": summary["total_matches"],
            }
        )

    rankings.sort(key=lambda item: (item["win_rate"], item["total_matches"], item["wins"]), reverse=True)
    return rankings
