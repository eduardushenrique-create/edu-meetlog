from __future__ import annotations

from pathlib import Path
from typing import Any

from transcription.models import normalize_segment


def transcribe_system_audio(
    model: Any,
    audio_path: Path | str,
    *,
    language: str = "pt",
    beam_size: int = 5,
    vad_filter: bool = False,
    time_offset: float = 0.0,
) -> dict[str, list[dict[str, Any]]]:
    segments, _ = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
    )

    result_segments: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        text = segment.text.strip()
        if not text:
            continue

        payload = {
            "start": float(segment.start) + time_offset,
            "end": float(segment.end) + time_offset,
            "text": text,
            "speaker": "system",
            "source": "system",
            "confidence": float(getattr(segment, "avg_logprob", 0.0) or 0.0),
        }

        result_segments.append(
            normalize_segment(
                payload,
                source="system",
                default_speaker="system",
                segment_index=index,
            )
        )

    return {"segments": result_segments}
