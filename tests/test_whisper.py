import pytest
import numpy as np
import time
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from faster_whisper import WhisperModel

class TestWhisperInference:
    """T6 — Whisper Inference Tests"""
    
    @pytest.fixture
    def model(self):
        import os
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        from gpu_detection import detect_device
        device_info = detect_device()
        
        return WhisperModel(
            "base",
            device=device_info["device"],
            compute_type=device_info["compute_type"]
        )
    
    @pytest.fixture
    def test_audio_file(self):
        return Path(__file__).parent.parent / "backend" / "recordings" / "2026-04-26_181807_mic.wav"
    
    def test_transcription_basic(self, model, test_audio_file):
        """Cenário 1 — Transcrição básica"""
        if not test_audio_file.exists():
            pytest.skip("Test audio file not found")
        
        segments, info = model.transcribe(
            str(test_audio_file),
            language="pt",
            vad_filter=False
        )
        
        results = [s.text for s in segments if s.text]
        
        assert isinstance(results, list)
    
    @pytest.mark.slow
    def test_latency(self, model, test_audio_file):
        """Cenário 2 — Latência"""
        if not test_audio_file.exists():
            pytest.skip("Test audio file not found")
        
        start = time.time()
        
        segments, info = model.transcribe(
            str(test_audio_file),
            language="pt",
            vad_filter=False
        )
        
        _ = [s for s in segments]
        
        elapsed = time.time() - start
        
        assert elapsed < 10, f"Expected <10s, got {elapsed:.1f}s"
    
    def test_gpu_activated(self):
        """Cenário 3 — GPU ativa"""
        from gpu_detection import detect_device
        
        info = detect_device()
        
        if info["cuda_available"]:
            assert info["device"] == "cuda"
            assert info["compute_type"] == "float16"
        else:
            assert info["device"] == "cpu"
    
    def test_fallback_cpu(self):
        """Cenário 4 — Fallback CPU"""
        import os
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        
        assert model is not None


class TestTranscription:
    """Integration tests for transcription"""
    
    def test_transcribe_audio_function(self):
        """Transcribe audio function"""
        from queue_worker import transcribe_audio
        
        test_file = Path(__file__).parent.parent / "backend" / "recordings" / "2026-04-26_181807_mic.wav"
        
        if not test_file.exists():
            pytest.skip("Test audio not found")
        
        result = transcribe_audio(test_file, "base", "mic")
        
        assert "segments" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])