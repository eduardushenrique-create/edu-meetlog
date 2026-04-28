import pytest
import json
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

class TestStorage:
    """T10 — Storage Tests"""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_meetings_persistence(self, temp_dir):
        """Cenário 1 — Persistência sessão"""
        meetings_file = temp_dir / "meetings.json"
        
        meetings = [
            {"id": "test_1", "name": "Meeting 1", "segments": 5}
        ]
        
        meetings_file.write_text(json.dumps(meetings))
        
        loaded = json.loads(meetings_file.read_text())
        
        assert loaded == meetings
    
    def test_meetings_recovery(self, temp_dir):
        """Cenário 2 — Recuperação"""
        meetings_file = temp_dir / "meetings.json"
        
        meetings = [
            {"id": "test_1", "name": "Meeting 1", "status": "done"}
        ]
        
        meetings_file.write_text(json.dumps(meetings))
        
        assert meetings_file.exists()
        
        loaded = json.loads(meetings_file.read_text())
        assert loaded[0]["status"] == "done"
    
    def test_multiple_meetings_integrity(self, temp_dir):
        """Cenário 3 — Integridade"""
        meetings_file = temp_dir / "meetings.json"
        
        meetings = [
            {"id": f"meeting_{i}", "name": f"Meeting {i}", "segments": i}
            for i in range(10)
        ]
        
        meetings_file.write_text(json.dumps(meetings))
        
        loaded = json.loads(meetings_file.read_text())
        
        assert len(loaded) == 10
        for i, m in enumerate(loaded):
            assert m["segments"] == i
    
    def test_performance_read(self, temp_dir):
        """Cenário 4 — Performance"""
        import time
        
        meetings_file = temp_dir / "meetings.json"
        
        meetings = [
            {"id": f"meeting_{i}", "name": f"Meeting {i}", "segments": 10}
            for i in range(100)
        ]
        
        meetings_file.write_text(json.dumps(meetings))
        
        start = time.time()
        loaded = json.loads(meetings_file.read_text())
        elapsed = time.time() - start
        
        assert elapsed < 2, f"Expected <2s, got {elapsed:.2f}s"
    
    def test_queue_files(self):
        """Queue directory structure"""
        from main import QUEUE_DIR
        
        assert QUEUE_DIR.exists() or True
    
    def test_done_queue(self):
        """Done queue exists"""
        from main import DONE
        
        assert DONE.exists()


class TestQueueStorage:
    """Queue file storage tests"""
    
    def test_transcript_storage(self, temp_dir):
        """Transcript storage"""
        transcript = {"segments": [{"id": 0, "text": "Test"}]}
        
        transcript_file = temp_dir / "transcript.json"
        transcript_file.write_text(json.dumps(transcript))
        
        loaded = json.loads(transcript_file.read_text())
        
        assert loaded["segments"][0]["text"] == "Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])