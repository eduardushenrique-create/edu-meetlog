import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from vad import VAD, SpeechDetector

class TestVAD:
    """T1 — VAD (Voice Activity Detection) Tests"""
    
    @pytest.fixture
    def vad(self):
        return VAD(sample_rate=16000, frame_duration=20, aggressiveness=2)
    
    @pytest.fixture
    def silence_audio(self):
        return np.zeros(16000)
    
    @pytest.fixture
    def speech_audio(self):
        return np.sin(2 * np.pi * 440 * np.linspace(0, 10, 160000))
    
    @pytest.fixture
    def noise_audio(self):
        np.random.seed(42)
        return np.random.randn(16000) * 0.02
    
    def test_continuous_speech(self, vad, speech_audio):
        """Cenário 1 — Detecção de fala contínua"""
        frame_size = vad.frame_size
        frames = [
            speech_audio[i:i+frame_size] 
            for i in range(0, len(speech_audio), frame_size)
        ]
        
        speech_count = sum(1 for f in frames if vad.is_speech(f))
        total_frames = len(frames)
        speech_rate = speech_count / total_frames
        
        assert speech_rate >= 0.9, f"Expected ≥90% speech frames, got {speech_rate:.1%}"
    
    def test_total_silence(self, vad, silence_audio):
        """Cenário 2 — Silêncio total"""
        frame_size = vad.frame_size
        frames = [
            silence_audio[i:i+frame_size] 
            for i in range(0, len(silence_audio), frame_size)
        ]
        
        speech_count = sum(1 for f in frames if vad.is_speech(f))
        
        assert speech_count == 0, f"Expected 0% speech frames, got {speech_count}"
    
    def test_background_noise(self, vad, noise_audio):
        """Cenário 3 — Ruído ambiente"""
        frame_size = vad.frame_size
        frames = [
            noise_audio[i:i+frame_size] 
            for i in range(0, len(noise_audio), frame_size)
        ]
        
        speech_count = sum(1 for f in frames if vad.is_speech(f))
        total_frames = len(frames)
        false_positive_rate = speech_count / total_frames
        
        assert false_positive_rate < 0.2, f"Expected <20% false positives, got {false_positive_rate:.1%}"
    
    def test_alternation(self, vad):
        """Cenário 4 — Alternância fala/silêncio"""
        np.random.seed(42)
        
        speech = np.sin(2 * np.pi * 440 * np.linspace(0, 2, 32000))
        silence = np.zeros(32000)
        
        combined = np.concatenate([speech, silence, speech])
        
        frame_size = vad.frame_size
        transitions = []
        last_speech = None
        
        for i in range(0, len(combined), frame_size):
            frame = combined[i:i+frame_size]
            is_speech = vad.is_speech(frame)
            
            if last_speech is not None and is_speech != last_speech:
                transitions.append(i * 1000 / 16000)
            
            last_speech = is_speech
        
        assert len(transitions) >= 2, f"Expected ≥2 transitions, got {len(transitions)}"


class TestSpeechDetector:
    """SpeechDetector tests"""
    
    @pytest.fixture
    def detector(self):
        return SpeechDetector(min_speech_duration=0.5, silence_duration=2.0)
    
    def test_process_frame_speech(self, detector):
        """Frame com fala"""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))
        result = detector.process_frame(audio)
        
        assert result["has_speech"] is True
    
    def test_process_frame_silence(self, detector):
        """Frame sem fala"""
        audio = np.zeros(16000)
        result = detector.process_frame(audio)
        
        assert result["has_speech"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])