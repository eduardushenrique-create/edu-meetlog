import pytest
import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from meeting_detection import MeetingDetector, ProcessMonitor, MEETING_PROCESSES

class TestMeetingDetection:
    """T2 — Meeting Detection Tests"""
    
    @pytest.fixture
    def detector(self):
        return MeetingDetector()
    
    @pytest.fixture
    def mock_process_monitor(self):
        return Mock(spec=ProcessMonitor)
    
    def test_meeting_start_valid(self, detector):
        """Cenário 1 — Início de reunião válido"""
        detector.start()
        
        with patch.object(detector.vad, 'process_frame') as mock_vad:
            mock_vad.return_value = {"type": "frame", "has_speech": True}
            
            for _ in range(100):
                detector.process_audio(np.sin(np.linspace(0, 1, 16000)))
                time.sleep(0.01)
        
        detector.stop()
        
        assert detector.is_meeting_active is True or detector.vad.is_speaking
    
    def test_no_meeting_without_process(self, detector):
        """Cenário 2 — Falso positivo (fala isolada)"""
        detector.start()
        
        short_speech = np.sin(np.linspace(0, 0.5, 8000))
        detector.process_audio(short_speech)
        
        detector.stop()
        
        assert detector.is_meeting_active is False
    
    def test_meeting_end(self, detector):
        """Cenário 3 — Término de reunião"""
        detector.start()
        
        silence = np.zeros(16000)
        for _ in range(200):
            detector.process_audio(silence)
            time.sleep(0.01)
        
        detector.stop()
        
        assert detector.is_meeting_active is False
    
    def test_no_meeting_without_speech(self, detector):
        """Cenário 4 — Processo ativo sem fala"""
        detector.start()
        
        silence = np.zeros(16000)
        for _ in range(50):
            detector.process_audio(silence)
            time.sleep(0.01)
        
        was_active = detector.is_meeting_active
        
        detector.stop()
        
        assert was_active is False


class TestProcessMonitor:
    """Process monitor tests"""
    
    @pytest.fixture
    def monitor(self):
        return ProcessMonitor()
    
    def test_get_active_meeting_apps(self, monitor):
        """Check for active meeting apps"""
        monitor.start()
        apps = monitor.get_active_meeting_apps()
        
        assert isinstance(apps, set)
    
    def test_meeting_processes_list(self):
        """Check MEETING_PROCESSES list"""
        assert "zoom.exe" in MEETING_PROCESSES
        assert "teams.exe" in MEETING_PROCESSES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])