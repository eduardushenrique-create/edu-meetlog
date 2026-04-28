from __future__ import annotations

import hashlib
from typing import Any, Literal, Mapping

SegmentSource = Literal["mic", "system", "mixed"]

DEFAULT_SPEAKER_BY_SOURCE: dict[SegmentSource, str] = {
    "mic": "user",
    "system": "system",
    "mixed": "user",
}

SUPPORTED_SOURCES = set(DEFAULT_SPEAKER_BY_SOURCE.keys())


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_segment_id(
    source: SegmentSource,
    start: float,
    end: float,
    text: str,
    segment_index: int = 0,
) -> str:
    normalized_text = " ".join(text.lower().split())
    digest = hashlib.sha1(normalized_text.encode("utf-8")).hexdigest()[:10]
    return f"{source}-{start:.3f}-{end:.3f}-{segment_index}-{digest}"


def segment_sort_key(segment: Mapping[str, Any]) -> tuple[float, float, str, str, str]:
    return (
        _safe_float(segment.get("start"), 0.0),
        _safe_float(segment.get("end"), 0.0),
        str(segment.get("source", "")),
        str(segment.get("speaker", "")),
        str(segment.get("text", "")),
    )


def segment_key(segment: Mapping[str, Any]) -> str:
    text = " ".join(str(segment.get("text", "")).strip().lower().split())
    return (
        f"{segment.get('source', '')}|"
        f"{_safe_float(segment.get('start'), 0.0):.3f}|"
        f"{_safe_float(segment.get('end'), 0.0):.3f}|"
        f"{text}"
    )


def normalize_segment(
    segment: Mapping[str, Any],
    source: SegmentSource,
    default_speaker: str,
    segment_index: int = 0,
) -> dict[str, Any]:
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source '{source}'")

    text = str(segment.get("text", "")).strip()
    start = max(0.0, _safe_float(segment.get("start"), 0.0))
    end = max(start, _safe_float(segment.get("end"), start))
    speaker = str(segment.get("speaker") or default_speaker).strip() or default_speaker

    normalized: dict[str, Any] = {
        "id": str(
            segment.get("id")
            or build_segment_id(source, start, end, text, segment_index=segment_index)
        ),
        "start": round(start, 3),
        "end": round(end, 3),
        "text": text,
        "source": source,
        "speaker": speaker,
    }

    confidence = segment.get("confidence")
    if confidence is not None:
        normalized["confidence"] = round(_safe_float(confidence, 0.0), 6)

    energy = segment.get("energy")
    if energy is not None:
        normalized["energy"] = round(_safe_float(energy, 0.0), 6)

    return normalized
