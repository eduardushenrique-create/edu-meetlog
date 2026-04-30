import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from diarization import (
    DiarizationEngine,
    SpeakerDiarizer,
    align_speakers_to_transcript,
    align_transcript_with_diarization,
)
from vad import VAD

class TestDiarization:
    """T8 — Diarization Tests"""
    
    @pytest.fixture
    def diarizer(self):
        return SpeakerDiarizer(sample_rate=16000)
    
    def test_process_audio(self, diarizer):
        """Process audio returns data"""
        audio = np.random.randn(16000)
        result = diarizer.process_audio(audio, "mic")
        
        assert result is not None
        assert "source" in result
    
    def test_energy_history(self, diarizer):
        """Energy tracking"""
        audio = np.sin(np.linspace(0, 10, 16000))
        
        for _ in range(10):
            diarizer.process_audio(audio, "mic")
        
        assert len(diarizer.energy_history["mic"]) > 0
    
    def test_get_active_speaker(self, diarizer):
        """Active speaker detection"""
        audio = np.sin(np.linspace(0, 10, 16000)) * 0.5
        
        diarizer.process_audio(audio, "mic")
        
        active = diarizer.get_active_speaker()
        
        assert active is not None
    
    def test_two_speakers(self, diarizer):
        """Cenário 1 — Dois speakers"""
        audio1 = np.sin(np.linspace(0, 5, 80000))
        
        diarizer.process_audio(audio1[:16000], "mic")
        diarizer.process_audio(audio1[16000:16000+16000], "system")
        
        energies = diarizer.energy_history
        
        assert "mic" in energies or "system" in energies


class TestAlignment:
    """T9 — Alignment Tests"""
    
    def test_alignment_with_speakers(self):
        """Cenário 1 — Matching correto"""
        segments = [
            {"id": 0, "start": 0, "end": 5, "speaker": "user", "text": "Olá"},
            {"id": 1, "start": 5, "end": 10, "speaker": "system", "text": "Legenda"},
        ]
        
        aligned = align_speakers_to_transcript(segments, {}, {})
        
        assert aligned[0]["speaker"] == "user"
        assert aligned[1]["speaker"] == "system"
    
    def test_alignment_caption_detection(self):
        """Caption detection"""
        segments = [
            {"id": 0, "start": 0, "end": 3, "text": "Legenda Adriana Zanotto"},
        ]
        
        aligned = align_speakers_to_transcript(segments, {}, {})
        
        assert aligned[0]["speaker"] == "system"
    
    def test_alignment_mic_detection(self):
        """Mic/USER detection"""
        segments = [
            {"id": 0, "start": 0, "end": 3, "text": "Vamos lá"},
        ]
        
        aligned = align_speakers_to_transcript(segments, {}, {})
        
        assert aligned[0]["speaker"] == "user"
    
    def test_alignment_fallback(self):
        """Cenário 3 — Sem diarização"""
        segments = []
        
        aligned = align_speakers_to_transcript(segments, {}, {})
        
        assert aligned == []

    def test_temporal_overlap_alignment(self):
        segments = [
            {"id": 0, "start": 0, "end": 4, "speaker": "unknown", "text": "A"},
            {"id": 1, "start": 4, "end": 8, "speaker": "unknown", "text": "B"},
        ]
        diarization = [
            {"start": 0, "end": 3.5, "speaker": "SPEAKER_00"},
            {"start": 4.5, "end": 8, "speaker": "SPEAKER_01"},
        ]

        aligned = align_transcript_with_diarization(segments, diarization)

        assert aligned[0]["speaker"] == "SPEAKER_00"
        assert aligned[1]["speaker"] == "SPEAKER_01"

    def test_engine_can_disable_pyannote(self):
        engine = DiarizationEngine(use_pyannote=False)

        assert engine.pipeline is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
