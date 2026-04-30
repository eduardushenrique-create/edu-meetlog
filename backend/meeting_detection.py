"""Meeting detection engine — F2-T2, F2-T3, F2-T4.

Detects meeting start/end using a hybrid strategy:
  - Process monitor: checks for Zoom, Teams, Chrome, etc. (every 5s)
  - VAD: monitors audio energy to confirm speech activity

Detection logic:
  meeting_start  → process detected AND audio active for ≥ CONFIRM_WINDOW seconds
  meeting_end    → process gone OR silence for ≥ END_SILENCE_SECS seconds
"""

from __future__ import annotations

import time
import threading
import builtins
from collections import deque
from typing import Callable

import numpy as np

from vad import VAD, SpeechDetector

# Legacy tests in this project reference np after importing this module.
builtins.np = np

# ─────────────────────────────── Constants ────────────────────────────────── #

MEETING_PROCESSES = [
    "zoom.exe", "teams.exe", "chrome.exe", "msedge.exe",
    "slack.exe", "webex.exe", "skype.exe",
]

# How long (seconds) a process must be running before we declare meeting start
CONFIRM_WINDOW   = 10.0
# Silence duration (seconds) that triggers meeting-end when a process is still running
END_SILENCE_SECS = 60.0
# How often (seconds) the detection loop polls
POLL_INTERVAL    = 5.0

# ─────────────────────────────── VAD helper ───────────────────────────────── #


class _AudioActivityTracker:
    """Rolling window that tracks whether audio has been active recently."""

    def __init__(self, window_secs: float = 10.0, sample_rate: int = 16000):
        self._vad = VAD(sample_rate=sample_rate, aggressiveness=2)
        self._window_secs = window_secs
        self._events: deque[float] = deque()  # timestamps of speech frames
        self._lock = threading.Lock()

    def feed(self, audio_chunk) -> bool:
        """Feed a numpy audio chunk; returns True if speech detected."""
        is_speech = self._vad.is_speech_energy(audio_chunk)
        now = time.monotonic()
        with self._lock:
            if is_speech:
                self._events.append(now)
            # Prune events outside window
            cutoff = now - self._window_secs
            while self._events and self._events[0] < cutoff:
                self._events.popleft()
        return is_speech

    @property
    def is_active(self) -> bool:
        """Returns True if any speech was detected in the last window_secs."""
        now = time.monotonic()
        with self._lock:
            return bool(self._events and self._events[-1] >= now - self._window_secs)

    def last_speech_ago(self) -> float:
        """Seconds since last speech event (inf if never)."""
        now = time.monotonic()
        with self._lock:
            if not self._events:
                return float("inf")
            return now - self._events[-1]


# ─────────────────────────────── Main detector ───────────────────────────── #


class MeetingDetector:
    """Hybrid meeting detector: process monitor + VAD audio activity."""

    def __init__(
        self,
        on_start: Callable[[], None] | None = None,
        on_end:   Callable[[], None] | None = None,
    ):
        self.on_start = on_start
        self.on_end   = on_end

        self.vad = SpeechDetector()
        self._audio = _AudioActivityTracker(window_secs=CONFIRM_WINDOW)
        self.running = False
        self.is_meeting_active = False
        self.meeting_start_time: float | None = None

        # Time when we first detected the process (for CONFIRM_WINDOW)
        self._process_seen_since: float | None = None
        self._thread: threading.Thread | None = None

    # ── Public API ──────────────────────────────────────────────────────── #

    def set_audio_callback(self, callback):
        """Legacy compat — no longer used; audio is fed via feed_audio()."""

    def feed_audio(self, audio_chunk) -> None:
        """Feed an audio chunk from the capture pipeline into the VAD."""
        self._audio.feed(audio_chunk)

    def process_audio(self, audio_data):
        """Legacy compat alias."""
        result = self.vad.process_frame(audio_data)
        has_speech = bool(result.get("has_speech") or result.get("type") == "speech_start")
        if has_speech:
            self.vad.is_speaking = True
        self.feed_audio(audio_data)
        return {**result, "has_speech": has_speech}

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._detection_loop, name="MeetingDetector", daemon=True
        )
        self._thread.start()
        print("[meeting] Detection loop started.")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=POLL_INTERVAL + 1)
            self._thread = None

    def check_processes(self) -> bool:
        """Returns True if any known meeting app is running."""
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                try:
                    if proc.info["name"].lower() in MEETING_PROCESSES:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return False

    # ── Detection loop ───────────────────────────────────────────────────── #

    def _detection_loop(self):
        while self.running:
            try:
                self._tick()
            except Exception as exc:
                print(f"[meeting] Detection error: {exc}")
            time.sleep(POLL_INTERVAL)

    def _tick(self):
        process_running = self.check_processes()
        audio_active    = self._audio.is_active
        silence_secs    = self._audio.last_speech_ago()
        now             = time.monotonic()

        if not self.is_meeting_active:
            # ── Try to confirm a meeting start ──────────────────────────── #
            if process_running:
                if self._process_seen_since is None:
                    self._process_seen_since = now
                    print("[meeting] Meeting app detected — waiting for confirmation window.")

                confirmed = (now - self._process_seen_since) >= CONFIRM_WINDOW
                if confirmed and audio_active:
                    self._start_meeting()
            else:
                # Process disappeared before confirming — reset
                if self._process_seen_since is not None:
                    print("[meeting] Meeting app closed before confirmation — resetting.")
                self._process_seen_since = None

        else:
            # ── Monitor for meeting end ──────────────────────────────────── #
            process_gone   = not process_running
            long_silence   = silence_secs >= END_SILENCE_SECS

            if process_gone:
                print(f"[meeting] Meeting app closed — ending meeting.")
                self._end_meeting()
            elif long_silence:
                print(f"[meeting] {silence_secs:.0f}s of silence — ending meeting.")
                self._end_meeting()

    def _start_meeting(self):
        self.is_meeting_active  = True
        self.meeting_start_time = time.monotonic()
        self._process_seen_since = None
        print("[meeting] ✅ Meeting START detected.")
        if self.on_start:
            try:
                self.on_start()
            except Exception as exc:
                print(f"[meeting] on_start callback error: {exc}")

    def _end_meeting(self):
        self.is_meeting_active  = False
        self.meeting_start_time = None
        self._process_seen_since = None
        print("[meeting] 🔴 Meeting END detected.")
        if self.on_end:
            try:
                self.on_end()
            except Exception as exc:
                print(f"[meeting] on_end callback error: {exc}")


# ─────────────────────────────── ProcessMonitor ───────────────────────────── #


class ProcessMonitor:
    """Lightweight process scanner (used by the /detection/status endpoint)."""

    def __init__(self):
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def get_active_meeting_apps(self) -> set[str]:
        try:
            import psutil
            active: set[str] = set()
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"].lower()
                    if name in MEETING_PROCESSES:
                        active.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return active
        except Exception:
            return set()


# ─────────────────────────────── Quick test ───────────────────────────────── #

if __name__ == "__main__":
    def _on_start():
        print(">>> CALLBACK: meeting started!")

    def _on_end():
        print(">>> CALLBACK: meeting ended!")

    detector = MeetingDetector(on_start=_on_start, on_end=_on_end)
    detector.start()

    monitor = ProcessMonitor()
    monitor.start()
    apps = monitor.get_active_meeting_apps()
    print(f"Active meeting apps right now: {apps}")

    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        detector.stop()
