import pytest
from fastapi.testclient import TestClient
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Adjust sys path so we can import the backend module directly
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from main import app, save_labels, save_meetings, load_meetings
from ai_engine import suggest_labels

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup - save current state
    try:
        from main import load_labels
        original_labels = load_labels()
        original_meetings = load_meetings()
    except Exception:
        original_labels = []
        original_meetings = []
    
    # Run test
    yield
    
    # Teardown - restore state
    try:
        save_labels(original_labels)
        save_meetings(original_meetings)
    except Exception:
        pass


class TestPhase3Labels:
    def test_create_and_get_label(self):
        # 1. Create label
        new_label = {
            "id": "test_label_1",
            "name": "Test Label",
            "color": "#FF0000"
        }
        res = client.post("/labels", json=new_label)
        assert res.status_code == 200
        assert res.json() == {"success": True}

        # 2. Get labels
        res = client.get("/labels")
        assert res.status_code == 200
        labels = res.json()
        assert any(l["id"] == "test_label_1" for l in labels)

    def test_delete_label(self):
        # Setup
        client.post("/labels", json={"id": "test_label_delete", "name": "To Delete", "color": "#000"})
        
        # Delete
        res = client.delete("/labels/test_label_delete")
        assert res.status_code == 200

        # Verify
        res = client.get("/labels")
        labels = res.json()
        assert not any(l["id"] == "test_label_delete" for l in labels)


class TestPhase3BulkActions:
    def setup_method(self):
        # Add some mock meetings
        self.mock_meetings = [
            {"id": "m1", "status": "done", "name": "Meeting 1", "date": "2023-01-01"},
            {"id": "m2", "status": "done", "name": "Meeting 2", "date": "2023-01-02"},
            {"id": "m3", "status": "done", "name": "Meeting 3", "date": "2023-01-03"}
        ]
        save_meetings(self.mock_meetings)

    def test_bulk_archive(self):
        # Request bulk archive for m1 and m2
        res = client.post("/meetings/bulk-archive", json={"ids": ["m1", "m2"]})
        assert res.status_code == 200
        assert res.json() == {"success": True, "archived": 2}

        # Verify state
        meetings = load_meetings()
        m1 = next(m for m in meetings if m["id"] == "m1")
        m3 = next(m for m in meetings if m["id"] == "m3")
        assert m1.get("archived") is True
        assert m3.get("archived", False) is False

    @patch('pathlib.Path.unlink')
    def test_bulk_delete(self, mock_unlink):
        # Request bulk delete for m1
        res = client.post("/meetings/bulk-delete", json={"ids": ["m1"]})
        assert res.status_code == 200
        assert res.json() == {"success": True, "deleted": 1}

        # Verify state
        meetings = load_meetings()
        ids = [m["id"] for m in meetings]
        assert "m1" not in ids
        assert "m2" in ids
        assert "m3" in ids


class TestPhase3AIEngine:
    def test_suggest_labels_regex_fallback(self):
        text = "Temos que revisar a proposta e enviar para o cliente amanhã urgente."
        available_labels = [
            {"id": "l1", "name": "Cliente", "color": "#000"},
            {"id": "l2", "name": "Urgente", "color": "#f00"},
            {"id": "l3", "name": "Financeiro", "color": "#0f0"}
        ]
        
        suggested_ids = suggest_labels(text, available_labels)
        
        # Should detect Cliente and Urgente based on the regex/keyword rules
        assert "l1" in suggested_ids
        assert "l2" in suggested_ids
        assert "l3" not in suggested_ids


class TestPhase3MeetingLabels:
    def setup_method(self):
        save_meetings([{"id": "mtg_label_test", "status": "done", "name": "Test", "date": ""}])

    def test_update_meeting_labels(self):
        res = client.post("/meetings/mtg_label_test/labels", json={"label_ids": ["tag1", "tag2"]})
        assert res.status_code == 200
        
        meetings = load_meetings()
        m = next(m for m in meetings if m["id"] == "mtg_label_test")
        assert m.get("labels") == ["tag1", "tag2"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
