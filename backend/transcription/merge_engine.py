from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Iterable, Literal, Mapping

from transcription.models import (
    DEFAULT_SPEAKER_BY_SOURCE,
    SegmentSource,
    normalize_segment,
    segment_key,
    segment_sort_key,
)

OverlapPolicy = Literal["keep_both", "select_best"]


@dataclass
class StreamMergeResult:
    merged_segments: list[dict[str, Any]]
    new_segments: list[dict[str, Any]]


class TranscriptMergeEngine:
    def __init__(
        self,
        overlap_policy: OverlapPolicy = "keep_both",
        score_resolver: Callable[[Mapping[str, Any]], tuple[float, float, float, int]] | None = None,
    ):
        self.overlap_policy = overlap_policy
        self.score_resolver = score_resolver
        self._stream_states: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def merge_segments(
        self,
        mic_segments: Iterable[Mapping[str, Any]],
        system_segments: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized_mic = self._normalize_source_segments(mic_segments, "mic")
        normalized_system = self._normalize_source_segments(system_segments, "system")

        combined = sorted(
            normalized_mic + normalized_system,
            key=segment_sort_key,
        )
        deduped = self._deduplicate(combined)
        return self._apply_overlap_policy(deduped)

    def merge_by_source(
        self,
        segments_by_source: Mapping[SegmentSource, Iterable[Mapping[str, Any]]],
    ) -> list[dict[str, Any]]:
        mic_segments = segments_by_source.get("mic", [])
        system_segments = segments_by_source.get("system", [])
        return self.merge_segments(mic_segments, system_segments)

    def merge_incremental(
        self,
        stream_id: str,
        source: SegmentSource,
        incoming_segments: Iterable[Mapping[str, Any]],
    ) -> StreamMergeResult:
        normalized_incoming = self._normalize_source_segments(incoming_segments, source)

        with self._lock:
            state = self._stream_states.setdefault(stream_id, self._new_stream_state())

            source_segments = state["segments_by_source"][source]
            source_known_keys = state["known_keys_by_source"][source]

            for segment in normalized_incoming:
                key = segment_key(segment)
                if key in source_known_keys:
                    continue
                source_known_keys.add(key)
                source_segments.append(segment)

            merged_segments = self.merge_segments(
                state["segments_by_source"]["mic"],
                state["segments_by_source"]["system"],
            )

            new_segments: list[dict[str, Any]] = []
            emitted_keys = state["emitted_keys"]
            for segment in merged_segments:
                key = segment_key(segment)
                if key in emitted_keys:
                    continue
                emitted_keys.add(key)
                new_segments.append(segment)

            state["last_merged"] = merged_segments

        return StreamMergeResult(merged_segments=merged_segments, new_segments=new_segments)

    def get_stream_segments(self, stream_id: str) -> list[dict[str, Any]]:
        with self._lock:
            state = self._stream_states.get(stream_id)
            if not state:
                return []
            return list(state.get("last_merged", []))

    def clear_stream(self, stream_id: str) -> None:
        with self._lock:
            self._stream_states.pop(stream_id, None)

    def _new_stream_state(self) -> dict[str, Any]:
        return {
            "segments_by_source": {
                "mic": [],
                "system": [],
            },
            "known_keys_by_source": {
                "mic": set(),
                "system": set(),
            },
            "emitted_keys": set(),
            "last_merged": [],
        }

    def _normalize_source_segments(
        self,
        segments: Iterable[Mapping[str, Any]],
        source: SegmentSource,
    ) -> list[dict[str, Any]]:
        default_speaker = DEFAULT_SPEAKER_BY_SOURCE[source]

        normalized: list[dict[str, Any]] = []
        for index, segment in enumerate(segments):
            standardized = normalize_segment(
                segment,
                source=source,
                default_speaker=default_speaker,
                segment_index=index,
            )
            if not standardized["text"]:
                continue
            normalized.append(standardized)

        return normalized

    def _deduplicate(self, segments: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for segment in segments:
            key = segment_key(segment)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(dict(segment))

        return deduped

    def _apply_overlap_policy(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.overlap_policy == "keep_both" or len(segments) <= 1:
            return segments

        resolved: list[dict[str, Any]] = []
        for segment in segments:
            if not resolved:
                resolved.append(segment)
                continue

            previous = resolved[-1]
            if not self._segments_overlap(previous, segment):
                resolved.append(segment)
                continue

            decision = self._resolve_overlap(previous, segment)
            if isinstance(decision, list):
                resolved[-1:] = decision
            elif decision is previous:
                continue
            else:
                resolved[-1] = decision

        return sorted(resolved, key=segment_sort_key)

    def _resolve_overlap(
        self,
        previous: Mapping[str, Any],
        current: Mapping[str, Any],
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        if self.overlap_policy == "keep_both":
            return [previous, current]

        previous_score = self._segment_score(previous)
        current_score = self._segment_score(current)

        if current_score > previous_score:
            return current
        if previous_score > current_score:
            return previous
        return [previous, current]

    def _segment_score(self, segment: Mapping[str, Any]) -> tuple[float, float, float, int]:
        if self.score_resolver is not None:
            return self.score_resolver(segment)

        confidence = float(segment.get("confidence", 0.0) or 0.0)
        energy = float(segment.get("energy", 0.0) or 0.0)
        duration = max(0.0, float(segment.get("end", 0.0) or 0.0) - float(segment.get("start", 0.0) or 0.0))
        text_length = len(str(segment.get("text", "")))
        return (confidence, energy, duration, text_length)

    @staticmethod
    def _segments_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        left_start = float(left.get("start", 0.0) or 0.0)
        left_end = float(left.get("end", left_start) or left_start)
        right_start = float(right.get("start", 0.0) or 0.0)
        right_end = float(right.get("end", right_start) or right_start)

        return left_start < right_end and right_start < left_end


def merge_segments(
    mic_segments: Iterable[Mapping[str, Any]],
    system_segments: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    engine = TranscriptMergeEngine(overlap_policy="keep_both")
    return engine.merge_segments(mic_segments, system_segments)
