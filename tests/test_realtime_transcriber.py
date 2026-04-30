import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from realtime_transcriber import RealtimeTranscriber


class TestRealtimeTranscriber:
    def test_trim_silence_preserves_speech_offset(self):
        sample_rate = 16000
        silence = np.zeros(sample_rate * 2, dtype=np.float32)
        speech = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate)).astype(np.float32) * 0.3
        audio = np.concatenate([silence, speech])

        trimmed, offset = RealtimeTranscriber._trim_silence(audio, sample_rate=sample_rate)

        assert 1.8 <= offset <= 2.0
        assert len(trimmed) < len(audio)

    def test_trim_silence_keeps_plain_speech_near_zero(self):
        sample_rate = 16000
        speech = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate)).astype(np.float32) * 0.3

        _, offset = RealtimeTranscriber._trim_silence(speech, sample_rate=sample_rate)

        assert offset == 0.0
