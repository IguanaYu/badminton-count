import os
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure we use a temporary database for tests
TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ["BADMINTON_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def get_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_login_and_list_matches():
    with TestClient(app) as client:
        token = get_token(client, "admin", "admin123")
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/matches/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) == 0

        players_to_create = [
            {
                "username": "test_player_a",
                "full_name": "Test Player A",
                "gender": "male",
                "password": "playerpass123",
                "can_record": False,
            },
            {
                "username": "test_player_b",
                "full_name": "Test Player B",
                "gender": "female",
                "password": "playerpass123",
                "can_record": False,
            },
        ]

        created_players = {}
        for payload in players_to_create:
            create_resp = client.post("/api/users/", json=payload, headers=auth_headers)
            assert create_resp.status_code == 200, create_resp.text
            created = create_resp.json()
            created_players[created["username"]] = created["id"]

        payload = {
            "played_at": datetime.utcnow().isoformat(),
            "session_number": 5,
            "match_type": "singles",
            "side_a_players": [created_players["test_player_a"]],
            "side_b_players": [created_players["test_player_b"]],
            "score_a": 21,
            "score_b": 19,
            "notes": "Test singles match",
        }
        create_resp = client.post(
            "/api/matches/",
            json=payload,
            headers=auth_headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        created = create_resp.json()
        assert created["session_number"] == 5
        assert created["score_a"] == 21
        assert created["winner_side"] == "A"

        # Rankings should include players with win rate field
        rankings_resp = client.get("/api/stats/rankings")
        assert rankings_resp.status_code == 200
        rankings = rankings_resp.json()
        assert any(item["full_name"] == "Test Player A" for item in rankings)

        # Export endpoints should return excel content
        export_resp = client.get("/api/exports/me/summary", headers=auth_headers)
        assert export_resp.status_code == 200
        assert (
            export_resp.headers["content-type"].startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
