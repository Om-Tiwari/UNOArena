import pytest
from fastapi.testclient import TestClient

import main as backend_main


class FakeLLMPlayer:
    def __init__(self, *args, **kwargs):
        self.model_name = kwargs.get("model", "fake-model")

    def get_intelligent_move(self, game_state, player_cards):
        # Always return a valid play if possible, else draw
        if player_cards:
            return {
                "action": "play",
                "card_id": str(player_cards[0].get("id", "card_1")),
                "color": player_cards[0].get("color"),
                "reasoning": "Test move",
            }
        return {"action": "draw", "reasoning": "No cards"}

    def validate_move(self, move, game_state, player_cards):
        # Treat any 'play' with matching id as valid
        if getattr(move, "action", "draw") == "play":
            cid = str(getattr(move, "card_id", ""))
            ok = any(str(c.get("id")) == cid for c in player_cards)
            return (ok, None if ok else "Card not in hand")
        return (True, None)

    def get_game_analysis(self, game_state, player_cards):
        from LLMPlayer import GameAnalysis
        return GameAnalysis(
            best_cards_to_keep=[str(pc.get("id", "card_1")) for pc in player_cards[:2]],
            opponent_threat_level=3,
            strategic_notes="Test analysis",
        )


@pytest.fixture(autouse=True)
def client(monkeypatch):
    # Patch get_llm_player to avoid real initialization and API keys
    monkeypatch.setattr(backend_main, "get_llm_player", lambda *a, **k: FakeLLMPlayer(model=k.get("model")))
    return TestClient(backend_main.app)


def sample_payload():
    return {
        "gameState": {
            "currentPlayer": {
                "id": "bot",
                "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 5, "color": "red"},
                    {"id": "card_2", "action": "wild", "color": "black"},
                ],
            },
            "tableStack": [{"id": "top", "digit": 5, "color": "blue"}],
            "otherPlayers": [{"name": "Opponent", "cards": 3}],
            "direction": 1,
            "sumDrawing": 0,
            "lastPlayerDrew": False,
            "gamePhase": "playing",
        },
        "playerCards": [
            {"id": "card_1", "digit": 5, "color": "red"},
            {"id": "card_2", "action": "wild", "color": "black"},
        ],
        "provider": "gemini",
        "model": "gemini-2.5-pro",
    }


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_move_ok(client):
    res = client.post("/move", json=sample_payload())
    assert res.status_code == 200
    body = res.json()
    assert body["isValid"] is True
    assert body["action"] in ("play", "draw")
    assert body["provider"] == "gemini"
    assert body["model"]
    assert "reasoning" in body


def test_analysis_ok(client):
    payload = sample_payload()
    res = client.post("/analysis", json={
        "gameState": payload["gameState"],
        "playerCards": payload["playerCards"],
        "provider": payload["provider"],
        "model": payload["model"],
    })
    assert res.status_code == 200
    body = res.json()
    assert body["provider"] == "gemini"
    assert body["model"]
    analysis = body["analysis"]
    assert isinstance(analysis, dict)
    assert "best_cards_to_keep" in analysis
    assert "opponent_threat_level" in analysis
    assert "strategic_notes" in analysis
