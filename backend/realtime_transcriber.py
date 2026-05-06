from __future__ import annotations

import collections
import queue
import threading
from typing import Callable

import numpy as np
from faster_whisper import WhisperModel

from gpu_detection import detect_device

# Type alias for result callbacks: (source, segments) -> None
ResultCallback = Callable[[str, list[dict]], None]

_LATENCY_WINDOW = 30  # keep last N inference latencies for rolling stats


class LatencyMetrics:
    """Thread-safe rolling latency tracker."""

    def __init__(self, window: int = _LATENCY_WINDOW):
        self._lock = threading.Lock()
        self._samples: collections.deque[float] = collections.deque(maxlen=window)
        self._total = 0

    def record(self, elapsed_s: float) -> None:
        with self._lock:
            self._samples.append(elapsed_s)
            self._total += 1

    def stats(self) -> dict:
        with self._lock:
            if not self._samples:
                return {"last_ms": None, "avg_ms": None, "p95_ms": None, "total_chunks": self._total}
            arr = sorted(self._samples)
            p95_idx = max(0, int(len(arr) * 0.95) - 1)
            return {
                "last_ms": round(arr[-1] * 1000),
                "avg_ms": round(sum(arr) / len(arr) * 1000),
                "p95_ms": round(arr[p95_idx] * 1000),
                "total_chunks": self._total,
            }

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()
            self._total = 0


class InferencePipeline:
    """CPU/GPU pipeline: N CPU preprocessing threads feed one GPU inference thread.

    Audio chunks are preprocessed (silence trim + normalize) on the calling thread,
    then enqueued for the single GPU worker. This keeps the GPU busy while CPU
    prepares the next chunk — eliminating the serialize-CPU-then-GPU bottleneck.
    """

    def __init__(self, model_name: str, beam_size: int = 1):
        self.model_name = model_name
        self.beam_size = beam_size
        self._q: queue.Queue = queue.Queue(maxsize=12)
        self._result_cb: ResultCallback | None = None
        self._model: WhisperModel | None = None
        self._running = False
        self._gpu_thread: threading.Thread | None = None
        self.metrics = LatencyMetrics()

    def start(self, result_callback: ResultCallback, shared_model: "WhisperModel | None" = None) -> None:
        if self._running:
            return
        self._result_cb = result_callback
        if shared_model is not None:
            self._model = shared_model
            print(f"[pipeline] Reusing shared WhisperModel — beam_size={self.beam_size}")
        else:
            device_info = detect_device()
            self._model = WhisperModel(
                self.model_name,
                device=device_info["device"],
                compute_type=device_info["compute_type"],
            )
            print(f"[pipeline] GPU worker started — device={device_info['device']} beam_size={self.beam_size}")
        self._running = True
        self._gpu_thread = threading.Thread(target=self._gpu_worker, daemon=True)
        self._gpu_thread.start()

    def stop(self) -> None:
        self._running = False
        self.metrics.reset()
        try:
            self._q.put_nowait(None)  # sentinel to unblock get()
        except queue.Full:
            pass

    def get_latency_stats(self) -> dict:
        """Return rolling inference latency stats for the status endpoint."""
        return self.metrics.stats()

    def submit(self, audio: np.ndarray, source: str, speaker: str, time_offset: float) -> None:
        """Enqueue preprocessed audio for GPU inference. Non-blocking; drops if full."""
        try:
            self._q.put_nowait((audio, source, speaker, time_offset))
        except queue.Full:
            # GPU is slower than audio capture — drop the oldest entry
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait((audio, source, speaker, time_offset))
            except queue.Full:
                pass

    # ------------------------------------------------------------------
    # CPU-side preprocessing (call from source capture threads)
    # ------------------------------------------------------------------

    @staticmethod
    def preprocess(audio_data) -> tuple[np.ndarray | None, float]:
        """Silence trim only — pure CPU/numpy, safe to call from any thread."""
        arr = np.asarray(audio_data, dtype=np.float32).flatten()
        if len(arr) < 1600:
            return None, 0.0

        sample_rate = 16000
        frame_ms = 100
        pad_ms = 120
        frame_size = max(1, int(sample_rate * frame_ms / 1000))
        frame_count = int(np.ceil(len(arr) / frame_size))
        rms_values = []

        for fi in range(frame_count):
            frame = arr[fi * frame_size:(fi + 1) * frame_size]
            if len(frame) == 0:
                continue
            rms_values.append(float(np.sqrt(np.mean(frame ** 2))))

        if not rms_values:
            return arr, 0.0

        rms = np.asarray(rms_values, dtype=np.float32)
        noise_floor = float(np.percentile(rms, 25))
        peak = float(np.max(rms))
        threshold = max(0.008, noise_floor + (peak - noise_floor) * 0.18)
        active = np.where(rms >= threshold)[0]
        if len(active) == 0:
            return None, 0.0

        pad_frames = int(np.ceil(pad_ms / frame_ms))
        first_frame = max(0, int(active[0]) - pad_frames)
        last_frame = min(frame_count - 1, int(active[-1]) + pad_frames)
        start_sample = first_frame * frame_size
        end_sample = min(len(arr), (last_frame + 1) * frame_size)
        trimmed = arr[start_sample:end_sample]
        if len(trimmed) < 1600:
            return None, 0.0
        return trimmed, start_sample / sample_rate

    # ------------------------------------------------------------------
    # GPU worker (single thread — serializes all model.transcribe calls)
    # ------------------------------------------------------------------

    def _gpu_worker(self) -> None:
        while self._running:
            # Drain up to 4 items per iteration (micro-batching reduces call overhead)
            batch: list[tuple] = []
            try:
                item = self._q.get(timeout=0.15)
                if item is None:
                    break
                batch.append(item)
            except queue.Empty:
                continue

            while len(batch) < 4:
                try:
                    item = self._q.get_nowait()
                    if item is None:
                        self._running = False
                        break
                    batch.append(item)
                except queue.Empty:
                    break

            for entry in batch:
                self._infer(*entry)

    def _infer(self, audio: np.ndarray, source: str, speaker: str, time_offset: float) -> None:
        if self._model is None or self._result_cb is None:
            return
        try:
            t_start = _monotonic()
            segments_iter, _ = self._model.transcribe(
                audio,
                language="pt",
                beam_size=self.beam_size,
                vad_filter=False,
            )
            results = []
            for i, seg in enumerate(segments_iter):
                text = seg.text.strip()
                if not text:
                    continue
                start = round(float(seg.start) + time_offset, 3)
                end = round(float(seg.end) + time_offset, 3)
                results.append({
                    "id": f"{source}-{start:.3f}-{end:.3f}-{i}",
                    "text": text,
                    "start": start,
                    "end": end,
                    "source": source,
                    "speaker": speaker,
                    "confidence": float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                    "partial": False,
                })
            elapsed = _monotonic() - t_start
            self.metrics.record(elapsed)
            if results:
                print(f"[pipeline] {source} {len(results)} seg(s) in {elapsed:.2f}s (avg {self.metrics.stats()['avg_ms']}ms)")
                self._result_cb(source, results)
        except Exception as exc:
            print(f"[pipeline] inference error ({source}): {exc}")


def _monotonic() -> float:
    import time
    return time.monotonic()


# ---------------------------------------------------------------------------
# Backward-compatible wrapper
# ---------------------------------------------------------------------------

class RealtimeTranscriber:
    """Thin wrapper around InferencePipeline kept for API compatibility.

    Callers that still use transcribe_chunk() synchronously will continue to work,
    but new code should use start(result_callback) + submit_chunk() for async path.
    """

    def __init__(self, model_name: str = "base", beam_size_realtime: int = 1):
        self.model_name = model_name
        self._beam_size = beam_size_realtime
        self._pipeline: InferencePipeline | None = None
        self.running = False
        self.callbacks: list = []
        # Legacy: lazy-loaded model for synchronous transcribe_chunk()
        self.model: WhisperModel | None = None

    def start(
        self,
        result_callback: ResultCallback | None = None,
        shared_model: "WhisperModel | None" = None,
    ) -> None:
        if self.running:
            return
        self.running = True
        self._pipeline = InferencePipeline(
            model_name=self.model_name,
            beam_size=self._beam_size,
        )
        effective_cb = result_callback or self._dispatch_to_callbacks
        self._pipeline.start(effective_cb, shared_model=shared_model)
        # Expose the loaded model for legacy callers
        self.model = self._pipeline._model

    def stop(self) -> None:
        self.running = False
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None
        self.model = None

    def get_latency_stats(self) -> dict:
        if self._pipeline is not None:
            return self._pipeline.get_latency_stats()
        return {"last_ms": None, "avg_ms": None, "p95_ms": None, "total_chunks": 0}

    def add_callback(self, callback: ResultCallback) -> None:
        self.callbacks.append(callback)

    def register_transcription_callback(self, audio_source: str, callback) -> None:
        self.add_callback(callback)

    def submit_chunk(
        self,
        audio_data,
        *,
        source: str = "mic",
        speaker: str | None = None,
        time_offset: float = 0.0,
    ) -> None:
        """Async path: preprocess on calling thread, submit to GPU queue."""
        if self._pipeline is None or audio_data is None:
            return
        if speaker is None:
            speaker = "user" if source == "mic" else "system"
        audio, speech_offset = InferencePipeline.preprocess(audio_data)
        if audio is None:
            return
        self._pipeline.submit(audio, source, speaker, time_offset + speech_offset)

    def transcribe_chunk(
        self,
        audio_data,
        *,
        source: str = "mic",
        speaker: str | None = None,
        time_offset: float = 0.0,
    ) -> list[dict] | None:
        """Synchronous path kept for backward compatibility.

        Routes through the async pipeline when available; falls back to direct
        model call if pipeline not started yet (e.g. during tests).
        """
        if self._pipeline is not None:
            # Use async path — caller is responsible for consuming via callback
            self.submit_chunk(audio_data, source=source, speaker=speaker, time_offset=time_offset)
            return None  # results come back via callback, not return value

        # Legacy fallback: direct synchronous inference (no pipeline)
        if audio_data is None or len(audio_data) < 1600:
            return None
        audio, speech_offset = InferencePipeline.preprocess(audio_data)
        if audio is None:
            return None
        if speaker is None:
            speaker = "user" if source == "mic" else "system"
        if self.model is None:
            device_info = detect_device()
            self.model = WhisperModel(
                self.model_name,
                device=device_info["device"],
                compute_type=device_info["compute_type"],
            )
        try:
            segments_iter, _ = self.model.transcribe(
                audio,
                language="pt",
                beam_size=self._beam_size,
                vad_filter=False,
            )
            results = []
            for i, seg in enumerate(segments_iter):
                text = seg.text.strip()
                if not text:
                    continue
                start = round(float(seg.start) + time_offset + speech_offset, 3)
                end = round(float(seg.end) + time_offset + speech_offset, 3)
                results.append({
                    "id": f"{source}-{start:.3f}-{end:.3f}-{i}",
                    "text": text,
                    "start": start,
                    "end": end,
                    "source": source,
                    "speaker": speaker,
                    "confidence": float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                    "partial": False,
                })
            return results if results else None
        except Exception as exc:
            print(f"Realtime transcription error: {exc}")
            return None

    def _dispatch_to_callbacks(self, source: str, segments: list[dict]) -> None:
        for cb in self.callbacks:
            try:
                cb(source, segments)
            except Exception as exc:
                print(f"[transcriber] callback error: {exc}")

    @staticmethod
    def _trim_silence(audio_data, sample_rate: int = 16000, frame_ms: int = 100, pad_ms: int = 120):
        """Kept for external callers; delegates to InferencePipeline.preprocess."""
        return InferencePipeline.preprocess(audio_data)
