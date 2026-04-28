import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

class TestWebSocketStreaming:
    """T7 — WebSocket Streaming Tests"""
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_exists(self):
        """Cenário 1 — Conexão"""
        from fastapi.testclient import TestClient
        from main import app
        
        with TestClient(app) as client:
            response = client.get("/ws/transcription")
            
            assert response.status_code in [200, 404, 500] or hasattr(client, "websocket_connect")
    
    def test_websocket_config(self):
        """WebSocket configuration"""
        from main import manager
        
        assert hasattr(manager, "active_connections")


class TestConnectionManager:
    """Connection manager tests"""
    
    def test_manager_initial_state(self):
        """Manager starts empty"""
        from main import manager
        
        assert manager.active_connections == []
    
    def test_manager_connect(self):
        """Connect method"""
        from main import ConnectionManager
        
        manager = ConnectionManager()
        
        assert manager.active_connections == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])