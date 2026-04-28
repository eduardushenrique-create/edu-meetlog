from __future__ import annotations

from threading import Thread

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

                start = round(float(segment.start) + time_offset, 3)
                end = round(float(segment.end) + time_offset, 3)
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
