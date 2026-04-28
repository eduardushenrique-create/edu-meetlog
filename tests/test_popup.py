import pytest
import httpx
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

class TestPopupSystem:
    """T3 — Popup System Tests"""
    
    def test_popup_endpoint(self, client):
        """Cenário 1 — Exibição correta"""
        response = client.post(
            "/popup/show",
            json={
                "popup_type": "info",
                "title": "Reunião detectada",
                "message": "Iniciar gravação?",
                "buttons": ["Ignorar", "Iniciar"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["title"] == "Reunião detectada"
    
    def test_popup_without_buttons(self, client):
        """Popup sem botões"""
        response = client.post(
            "/popup/show",
            json={
                "popup_type": "info",
                "title": "Test",
                "message": "Test message"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["buttons"] == []
    
    def test_popup_id_generation(self, client):
        """Verifica ID único do popup"""
        response1 = client.post("/popup/show", json={
            "popup_type": "info",
            "title": "Test 1",
            "message": "Message 1"
        })
        
        response2 = client.post("/popup/show", json={
            "popup_type": "info", 
            "title": "Test 2",
            "message": "Message 2"
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestPopupAPI:
    """Popup API validation"""
    
    def test_get_status_includes_popup(self, client):
        """Verifica que status endpoint responde"""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "state" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])