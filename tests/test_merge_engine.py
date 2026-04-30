import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from transcription.merge_engine import TranscriptMergeEngine, merge_segments


class TestTranscriptMergeEngine:
    def test_merge_orders_segments_by_start(self):
        mic_segments = [
            {"start": 4.0, "end": 5.0, "text": "mic-2", "speaker": "user"},
            {"start": 1.0, "end": 2.0, "text": "mic-1", "speaker": "user"},
        ]
        system_segments = [
            {"start": 2.5, "end": 3.5, "text": "sys-1", "speaker": "system"},
        ]

        merged = merge_segments(mic_segments, system_segments)

        assert [segment["text"] for segment in merged] == ["mic-1", "sys-1", "mic-2"]
        assert all(segment["source"] in {"mic", "system"} for segment in merged)

    def test_overlap_keep_both_by_default(self):
        engine = TranscriptMergeEngine(overlap_policy="keep_both")

        merged = engine.merge_segments(
            [{"start": 1.0, "end": 4.0, "text": "mic overlap"}],
            [{"start": 2.0, "end": 3.0, "text": "system overlap"}],
        )

        assert len(merged) == 2
        assert {segment["source"] for segment in merged} == {"mic", "system"}

    def test_overlap_select_best_uses_confidence(self):
        engine = TranscriptMergeEngine(overlap_policy="select_best")

        merged = engine.merge_segments(
            [{"start": 1.0, "end": 4.0, "text": "mic overlap", "confidence": 0.15}],
            [{"start": 1.1, "end": 3.8, "text": "system overlap", "confidence": 0.90}],
        )

        assert len(merged) == 1
        assert merged[0]["source"] == "system"
        assert merged[0]["text"] == "system overlap"

    def test_incremental_merge_emits_only_new_segments(self):
        engine = TranscriptMergeEngine(overlap_policy="keep_both")
        stream_id = "meeting_stream_1"

        first = engine.merge_incremental(
            stream_id,
            "mic",
            [{"start": 0.0, "end": 1.0, "text": "hello"}],
        )
        second = engine.merge_incremental(
            stream_id,
            "mic",
            [{"start": 0.0, "end": 1.0, "text": "hello"}],
        )
        third = engine.merge_incremental(
            stream_id,
            "system",
            [{"start": 1.1, "end": 2.0, "text": "oi"}],
        )

        assert len(first.new_segments) == 1
        assert len(second.new_segments) == 0
        assert len(third.new_segments) == 1
        assert len(third.merged_segments) == 2

    def test_incremental_merge_suppresses_shifted_text_duplicate(self):
        engine = TranscriptMergeEngine(overlap_policy="keep_both")
        stream_id = "meeting_stream_1"

        first = engine.merge_incremental(
            stream_id,
            "mic",
            [{"start": 13.56, "end": 18.0, "text": "Iniciando áudio do YouTube."}],
        )
        shifted_duplicate = engine.merge_incremental(
            stream_id,
            "mic",
            [{"start": 30.0, "end": 34.0, "text": "Iniciando áudio do YouTube."}],
        )

        assert len(first.new_segments) == 1
        assert shifted_duplicate.new_segments == []
        assert len(shifted_duplicate.merged_segments) == 1

    def test_output_contains_standard_segment_fields(self):
        merged = merge_segments(
            [{"start": 0.0, "end": 0.8, "text": "A"}],
            [{"start": 0.9, "end": 1.8, "text": "B"}],
        )

        for segment in merged:
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment
            assert "source" in segment
            assert "speaker" in segment
