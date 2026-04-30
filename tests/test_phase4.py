import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from main import (  # noqa: E402
    app,
    load_action_items,
    load_clients,
    load_meetings,
    load_people,
    load_stakeholders,
    save_action_items,
    save_clients,
    save_meetings,
    save_people,
    save_stakeholders,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def phase4_state_guard():
    original_clients = load_clients()
    original_people = load_people()
    original_stakeholders = load_stakeholders()
    original_action_items = load_action_items()
    original_meetings = load_meetings()

    yield

    save_clients(original_clients)
    save_people(original_people)
    save_stakeholders(original_stakeholders)
    save_action_items(original_action_items)
    save_meetings(original_meetings)


def test_create_phase4_core_entities():
    client_res = client.post(
        "/clients",
        json={"id": "client_acme", "name": "ACME", "aliases": ["Acme Corp"]},
    )
    assert client_res.status_code == 200

    person_res = client.post(
        "/people",
        json={"id": "person_ana", "name": "Ana Souza", "client_ids": ["client_acme"]},
    )
    assert person_res.status_code == 200

    stakeholder_res = client.post(
        "/stakeholders",
        json={
            "id": "stakeholder_ana_acme",
            "client_id": "client_acme",
            "person_id": "person_ana",
            "role": "Sponsor",
            "influence_level": "high",
            "is_primary": True,
        },
    )
    assert stakeholder_res.status_code == 200

    action_item_res = client.post(
        "/action-items",
        json={
            "id": "action_followup",
            "title": "Enviar proposta revisada",
            "client_id": "client_acme",
            "assignee_person_id": "person_ana",
            "status": "open",
            "priority": "high",
            "evidence": [{"excerpt": "Precisamos revisar a proposta ainda hoje."}],
        },
    )
    assert action_item_res.status_code == 200

    client_detail = client.get("/clients/client_acme")
    assert client_detail.status_code == 200
    body = client_detail.json()
    assert body["name"] == "ACME"
    assert len(body["stakeholders"]) == 1
    assert body["stakeholders"][0]["person_id"] == "person_ana"


def test_classify_meeting_and_calculate_client_indicators():
    save_clients([{"id": "client_beta", "name": "Beta", "aliases": [], "description": "", "labels": [], "active": True}])
    save_meetings(
        [
            {
                "id": "meeting_week_ext",
                "name": "Weekly sync",
                "date": "2026-04-28T10:00:00",
                "duration": "1:00:00",
                "status": "done",
                "archived": False,
                "client_id": "client_beta",
                "meeting_kind": "external",
            },
            {
                "id": "meeting_week_int",
                "name": "Internal prep",
                "date": "2026-04-29T09:00:00",
                "duration": "0:30:00",
                "status": "done",
                "archived": False,
                "client_id": "client_beta",
                "meeting_kind": "internal",
            },
            {
                "id": "meeting_month_ext",
                "name": "Kickoff",
                "date": "2026-04-05T11:00:00",
                "duration": "0:45:00",
                "status": "done",
                "archived": False,
                "client_id": "client_beta",
                "meeting_kind": "external",
            },
            {
                "id": "meeting_unclassified",
                "name": "New call",
                "date": "2026-04-29T14:00:00",
                "duration": "0:15:00",
                "status": "done",
                "archived": False,
            },
        ]
    )

    classify_res = client.post(
        "/meetings/meeting_unclassified/classification",
        json={"client_id": "client_beta", "meeting_kind": "external"},
    )
    assert classify_res.status_code == 200

    indicators_res = client.get("/clients/client_beta/indicators", params={"reference_date": "2026-04-29"})
    assert indicators_res.status_code == 200
    indicators = indicators_res.json()

    assert indicators["weekly_minutes"] == 105.0
    assert indicators["monthly_minutes"] == 150.0
    assert indicators["weekly_external_minutes"] == 75.0
    assert indicators["weekly_internal_minutes"] == 30.0
    assert indicators["meeting_count"] == 4
    assert "meeting_unclassified" in indicators["weekly_meeting_ids"]


def test_action_items_can_be_filtered_by_client_and_status():
    save_clients([{"id": "client_gamma", "name": "Gamma", "aliases": [], "description": "", "labels": [], "active": True}])
    save_action_items(
        [
            {"id": "a1", "title": "Pendente aberta", "client_id": "client_gamma", "status": "open"},
            {"id": "a2", "title": "Pendente concluída", "client_id": "client_gamma", "status": "done"},
            {"id": "a3", "title": "Outro cliente", "client_id": "client_other", "status": "open"},
        ]
    )

    res = client.get("/action-items", params={"client_id": "client_gamma", "status": "open"})
    assert res.status_code == 200
    items = res.json()

    assert len(items) == 1
    assert items[0]["id"] == "a1"
