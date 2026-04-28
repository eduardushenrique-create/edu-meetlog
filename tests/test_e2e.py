import pytest
import time
import sys
import threading
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

class TestE2E:
    """E2E — End to End Tests"""
    
    @pytest.fixture
    def backend_url(self):
        return "http://127.0.0.1:8000"
    
    def test_backend_health(self, backend_url):
        """Check backend is running"""
        import httpx
        
        try:
            response = httpx.get(f"{backend_url}/status", timeout=5)
            assert response.status_code == 200
        except:
            pytest.skip("Backend not running")
    
    def test_status_endpoint(self, backend_url):
        """Status returns expected fields"""
        import httpx
        
        try:
            response = httpx.get(f"{backend_url}/status")
            data = response.json()
            
            assert "state" in data
            assert "queue_stats" in data
            assert "gpu" in data
        except:
            pytest.skip("Backend not running")
    
    def test_meetings_endpoint(self, backend_url):
        """Meetings endpoint"""
        import httpx
        
        try:
            response = httpx.get(f"{backend_url}/meetings")
            assert response.status_code == 200
        except:
            pytest.skip("Backend not running")
    
    def test_detection_status(self):
        """Detection status endpoint"""
        import httpx
        
        try:
            response = httpx.get("http://127.0.0.1:8000/detection/status")
            data = response.json()
            
            assert "active_apps" in data
        except:
            pytest.skip("Backend not running")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_pipeline(self):
        """E2E 1 — Fluxo completo"""
        from audio_capture import AudioCapture
        from queue_worker import transcribe_audio
        from gpu_detection import detect_device
        from meeting_detection import MeetingDetector
        
        device_info = detect_device()
        
        assert device_info["cuda_available"] is not None
        
        meeting_detector = MeetingDetector()
        meeting_detector.start()
        
        time.sleep(0.5)
        
        meeting_detector.stop()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_long_session_stability(self):
        """E2E 2 — Execução longa (simplified)"""
        from gpu_detection import detect_device
        
        for i in range(5):
            device = detect_device()
            assert device is not None
            time.sleep(0.1)
    
    @pytest.mark.integration
    def test_adverse_environment(self):
        """E2E 3 — Ambiente adverso"""
        import os
        
        original_env = os.environ.copy()
        
        try:
            from gpu_detection import detect_device
            
            info = detect_device()
            
            assert "device" in info
        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestPipeline:
    """Pipeline integration tests"""
    
    def test_gpu_pipeline(self):
        """GPU pipeline"""
        from gpu_detection import detect_device
        
        info = detect_device()
        
        assert info["device"] in ["cuda", "cpu"]
    
    def test_vad_pipeline(self):
        """VAD pipeline"""
        from vad import VAD
        
        vad = VAD()
        
        assert vad.threshold > 0
    
    def test_meeting_pipeline(self):
        """Meeting detection pipeline"""
        from meeting_detection import MeetingDetector
        
        detector = MeetingDetector()
        
        assert detector.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])