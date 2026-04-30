from __future__ import annotations

from threading import Thread

import numpy as np
from faster_whisper import WhisperModel

from gpu_detection import detect_device


class RealtimeTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model: WhisperModel | None = None
        self.running = False
        self.callbacks: list = []

    def start(self):
        if self.running:
            return
        self.running = True
        device_info = detect_device()
        self.model = WhisperModel(
            self.model_name,
            device=device_info["device"],
            compute_type=device_info["compute_type"],
        )
        Thread(target=self._process_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def transcribe_chunk(
        self,
        audio_data,
        *,
        source: str = "mic",
        speaker: str | None = None,
        time_offset: float = 0.0,
    ):
        if self.model is None or audio_data is None or len(audio_data) < 1600:
            return None

        audio_data, speech_offset = self._trim_silence(audio_data)
        if audio_data is None or len(audio_data) < 1600:
            return None

        if speaker is None:
            speaker = "user" if source == "mic" else "system"

        try:
            segments, _ = self.model.transcribe(
                audio_data,
                language="pt",
                beam_size=5,
                vad_filter=False,
            )

            results = []
            for index, segment in enumerate(segments):
                text = segment.text.strip()
                if not text:
                    continue

                start = round(float(segment.start) + time_offset + speech_offset, 3)
                end = round(float(segment.end) + time_offset + speech_offset, 3)
                results.append(
                    {
                        "id": f"{source}-{start:.3f}-{end:.3f}-{index}",
                        "text": text,
                        "start": start,
                        "end": end,
                        "source": source,
                        "speaker": speaker,
                        "confidence": float(getattr(segment, "avg_logprob", 0.0) or 0.0),
                        "partial": False,
                    }
                )
            return results if results else None
        except Exception as exc:
            print(f"Realtime transcription error: {exc}")
            return None

    def _process_loop(self):
        print("Realtime transcription worker started")

    def register_transcription_callback(self, audio_source: str, callback):
        self.add_callback(callback)

    @staticmethod
    def _trim_silence(audio_data, sample_rate: int = 16000, frame_ms: int = 100, pad_ms: int = 120):
        arr = np.asarray(audio_data, dtype=np.float32).flatten()
        if len(arr) == 0:
            return arr, 0.0

        frame_size = max(1, int(sample_rate * frame_ms / 1000))
        frame_count = int(np.ceil(len(arr) / frame_size))
        rms_values = []

        for frame_index in range(frame_count):
            start = frame_index * frame_size
            frame = arr[start:start + frame_size]
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
            return arr, 0.0

        pad_frames = int(np.ceil(pad_ms / frame_ms))
        first_frame = max(0, int(active[0]) - pad_frames)
        last_frame = min(frame_count - 1, int(active[-1]) + pad_frames)
        start_sample = first_frame * frame_size
        end_sample = min(len(arr), (last_frame + 1) * frame_size)

        return arr[start_sample:end_sample], start_sample / sample_rate
