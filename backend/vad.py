"""Voice Activity Detection — F2-T1.

Uses webrtcvad (Google WebRTC VAD) when available, with a numpy RMS fallback.

webrtcvad requires:
  - 16-bit PCM audio (int16)
  - Sample rate: 8000, 16000, 32000, or 48000 Hz
  - Frame sizes: exactly 10ms, 20ms, or 30ms
  - Mono channel

Install: pip install webrtcvad-wheels
"""

from __future__ import annotations

import struct
from collections import deque
from typing import Optional

import numpy as np


# ─────────────────────────────── Core VAD ─────────────────────────────────── #


def _try_import_webrtcvad():
    """Import webrtcvad (or webrtcvad_wheels alias) if available."""
    try:
        import webrtcvad
        return webrtcvad
    except ImportError:
        pass
    try:
        import webrtcvad_wheels as webrtcvad
        return webrtcvad
    except ImportError:
        return None


_webrtcvad = _try_import_webrtcvad()


class VAD:
    """Voice Activity Detector.

    Uses WebRTC VAD when available; falls back to RMS energy threshold.

    Args:
        sample_rate:    Audio sample rate in Hz (default 16000).
        frame_duration: Frame size in ms — must be 10, 20, or 30 (default 20).
        aggressiveness: WebRTC aggressiveness 0–3. Higher = more aggressive
                        filtering (fewer false positives, more false negatives).
    """

    _VALID_FRAME_MS  = (10, 20, 30)
    _RMS_THRESHOLDS  = {0: 0.05, 1: 0.04, 2: 0.03, 3: 0.025}

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration: int = 20,
        aggressiveness: int = 2,
    ):
        if frame_duration not in self._VALID_FRAME_MS:
            raise ValueError(
                f"frame_duration must be one of {self._VALID_FRAME_MS}, got {frame_duration}"
            )

        self.sample_rate    = sample_rate
        self.frame_duration = frame_duration
        self.aggressiveness = aggressiveness
        self.frame_size     = int(sample_rate * frame_duration / 1000)

        # Try to initialise webrtcvad
        self._vad = None
        if _webrtcvad is not None:
            try:
                self._vad = _webrtcvad.Vad(aggressiveness)
                print(
                    f"[vad] Using WebRTC VAD (aggressiveness={aggressiveness}, "
                    f"frame={frame_duration}ms, sr={sample_rate}Hz)"
                )
            except Exception as exc:
                print(f"[vad] WebRTC VAD init failed ({exc}), using RMS fallback.")
        else:
            print("[vad] webrtcvad not installed — using RMS energy fallback.")

        self._rms_threshold = self._RMS_THRESHOLDS.get(aggressiveness, 0.03)
        self.threshold = self._rms_threshold

    # ── Public methods ─────────────────────────────────────────────────── #

    def is_speech(self, audio_frame) -> bool:
        """Detect speech in a single audio frame (numpy float32 or int16 array).

        The frame length should match frame_size samples.
        """
        rms_speech = self._rms_is_speech(audio_frame)
        if self._vad is not None:
            return self._webrtc_is_speech(audio_frame) or rms_speech
        return rms_speech

    def is_speech_energy(self, audio_frame) -> bool:
        """Alias kept for backward compat with _AudioActivityTracker."""
        return self.is_speech(audio_frame)

    # ── Internal ──────────────────────────────────────────────────────── #

    def _webrtc_is_speech(self, frame) -> bool:
        """Convert frame to int16 PCM bytes and run through WebRTC VAD."""
        try:
            arr = np.asarray(frame, dtype=np.float32).flatten()

            # Pad or truncate to exact frame_size
            if len(arr) < self.frame_size:
                arr = np.pad(arr, (0, self.frame_size - len(arr)))
            arr = arr[: self.frame_size]

            # Clip to [-1, 1] before converting to int16
            arr = np.clip(arr, -1.0, 1.0)
            pcm_bytes = (arr * 32767).astype(np.int16).tobytes()

            return self._vad.is_speech(pcm_bytes, self.sample_rate)
        except Exception:
            # Fall back to RMS on any error
            return self._rms_is_speech(frame)

    def _rms_is_speech(self, frame) -> bool:
        """Simple RMS energy threshold."""
        arr = np.asarray(frame, dtype=np.float32).flatten()
        if len(arr) == 0:
            return False
        rms = float(np.sqrt(np.mean(arr ** 2)))
        return rms > self._rms_threshold


# ─────────────────────────────── SpeechDetector ───────────────────────────── #


class SpeechDetector:
    """State machine that detects speech start/end events from a VAD stream.

    Emits:
        {"type": "speech_start"}        — first speech frame after silence
        {"type": "frame", "has_speech": bool}
        {"type": "speech_end", "audio": np.ndarray}  — after silence_duration
    """

    def __init__(
        self,
        sample_rate:        int   = 16000,
        min_speech_duration: float = 0.3,
        silence_duration:    float = 2.0,
    ):
        self.sample_rate         = sample_rate
        self.min_speech_duration = min_speech_duration
        self.silence_duration    = silence_duration

        self.vad            = VAD(sample_rate=sample_rate, aggressiveness=2)
        self.speech_buffer: deque = deque()
        self.silence_frames = 0
        self.is_speaking    = False

        # Silence threshold in frames (frame_duration=20ms)
        self._silence_threshold = int(silence_duration * 1000 / self.vad.frame_duration)

    def process_frame(self, audio_frame) -> dict:
        has_speech = self.vad.is_speech(audio_frame)

        if has_speech:
            if not self.is_speaking:
                self.is_speaking    = True
                self.silence_frames = 0
                self.speech_buffer.append(audio_frame)
                return {"type": "speech_start", "has_speech": True}
            self.speech_buffer.append(audio_frame)
            self.silence_frames = 0
        else:
            if self.is_speaking:
                self.silence_frames += 1
                if self.silence_frames >= self._silence_threshold:
                    self.is_speaking    = False
                    self.silence_frames = 0
                    if self.speech_buffer:
                        speech_data = np.concatenate(
                            [np.asarray(f).flatten() for f in self.speech_buffer]
                        )
                        self.speech_buffer.clear()
                        return {"type": "speech_end", "audio": speech_data}

        return {"type": "frame", "has_speech": has_speech}

    def reset(self):
        self.speech_buffer.clear()
        self.silence_frames = 0
        self.is_speaking    = False


# ─────────────────────────────── Quick test ───────────────────────────────── #

if __name__ == "__main__":
    vad = VAD()
    print(f"VAD backend: {'WebRTC' if vad._vad is not None else 'RMS fallback'}")
    print(f"Frame size : {vad.frame_size} samples")

    # Synthetic test: zeros = silence
    silence = np.zeros(vad.frame_size, dtype=np.float32)
    noise   = np.random.uniform(-0.5, 0.5, vad.frame_size).astype(np.float32)
    print(f"Silence frame -> speech: {vad.is_speech(silence)}")
    print(f"Noise frame   -> speech: {vad.is_speech(noise)}")

    detector = SpeechDetector()
    print("SpeechDetector ready.")
