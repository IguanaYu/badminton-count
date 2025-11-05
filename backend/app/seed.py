from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .auth.utils import get_password_hash
from .models import Gender, Match, MatchParticipant, MatchType, User, resolve_winner


DEFAULT_USERS = [
    {
        "username": "admin",
        "full_name": "Admin",
        "gender": "other",
        "password": "admin123",
        "is_admin": True,
        "is_root": True,
        "can_record": True,
    },
    {
        "username": "alice",
        "full_name": "Alice Chen",
        "gender": "female",
        "password": "password123",
        "can_record": True,
    },
    {
        "username": "bob",
        "full_name": "Bob Li",
        "gender": "male",
        "password": "password123",
        "can_record": True,
    },
    {
        "username": "carol",
        "full_name": "Carol Wang",
        "gender": "female",
        "password": "password123",
    },
    {
        "username": "dave",
        "full_name": "Dave Zhang",
        "gender": "male",
        "password": "password123",
    },
]


MATCH_BLUEPRINTS = [
    {
        "played_at": datetime.utcnow() - timedelta(days=10),
        "match_type": MatchType.singles,
        "side_a": ["alice"],
        "side_b": ["bob"],
        "score_a": 21,
        "score_b": 18,
        "session_number": 1,
        "notes": "Friendly training match",
    },
    {
        "played_at": datetime.utcnow() - timedelta(days=7, hours=2),
        "match_type": MatchType.doubles,
        "side_a": ["alice", "carol"],
        "side_b": ["bob", "dave"],
        "score_a": 19,
        "score_b": 21,
        "session_number": 2,
        "notes": "Weekly doubles showdown",
    },
    {
        "played_at": datetime.utcnow() - timedelta(days=5),
        "match_type": MatchType.one_vs_two,
        "side_a": ["alice"],
        "side_b": ["bob", "dave"],
        "score_a": 17,
        "score_b": 21,
        "session_number": 1,
        "notes": "Alice challenge match",
    },
    {
        "played_at": datetime.utcnow() - timedelta(days=3),
        "match_type": MatchType.singles,
        "side_a": ["carol"],
        "side_b": ["dave"],
        "score_a": 15,
        "score_b": 21,
        "session_number": 3,
        "notes": "Evening singles",
    },
    {
        "played_at": datetime.utcnow() - timedelta(days=1),
        "match_type": MatchType.doubles,
        "side_a": ["alice", "bob"],
        "side_b": ["carol", "dave"],
        "score_a": 22,
        "score_b": 20,
        "session_number": 4,
        "notes": "Close doubles battle",
    },
]


def seed_users(db: Session):
    if db.query(User).count() > 0:
        return

    created_users = {}
    for entry in DEFAULT_USERS:
        user = User(
            username=entry["username"],
            full_name=entry["full_name"],
            gender=Gender(entry["gender"]),
            hashed_password=get_password_hash(entry["password"]),
            is_admin=entry.get("is_admin", False),
            is_root=entry.get("is_root", False),
            can_record=entry.get("can_record", False),
        )
        db.add(user)
        db.flush()
        created_users[entry["username"]] = user

    db.commit()
    return created_users


def seed_matches(db: Session):
    if db.query(Match).count() > 0:
        return

    users = {user.username: user for user in db.query(User).all()}
    admin = users["admin"]

    for blueprint in MATCH_BLUEPRINTS:
        side_a_users = [users[name] for name in blueprint["side_a"]]
        side_b_users = [users[name] for name in blueprint["side_b"]]
        match = Match(
            played_at=blueprint["played_at"],
            session_number=blueprint["session_number"],
            match_type=blueprint["match_type"],
            score_a=blueprint["score_a"],
            score_b=blueprint["score_b"],
            winner_side=resolve_winner(blueprint["score_a"], blueprint["score_b"]),
            notes=blueprint["notes"],
            recorded_by_id=admin.id,
        )
        db.add(match)
        db.flush()

        for idx, user in enumerate(side_a_users, start=1):
            db.add(MatchParticipant(match_id=match.id, user_id=user.id, side="A", slot=idx))
        for idx, user in enumerate(side_b_users, start=1):
            db.add(MatchParticipant(match_id=match.id, user_id=user.id, side="B", slot=idx))

    db.commit()


def seed_data(db: Session):
    seed_users(db)
    seed_matches(db)
