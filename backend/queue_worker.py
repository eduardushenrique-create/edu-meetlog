import json
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Iterable

from faster_whisper import WhisperModel

from gpu_detection import detect_device
from transcription.merge_engine import TranscriptMergeEngine
from transcription.mic_worker import transcribe_mic_audio
from transcription.models import DEFAULT_SPEAKER_BY_SOURCE, SegmentSource, normalize_segment
from transcription.system_worker import transcribe_system_audio

QUEUE_DIR = Path(__file__).parent / "queue"
PENDING = QUEUE_DIR / "pending"
PROCESSING = QUEUE_DIR / "processing"
DONE = QUEUE_DIR / "done"
FAILED = QUEUE_DIR / "failed"

PENDING.mkdir(parents=True, exist_ok=True)
PROCESSING.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)
FAILED.mkdir(parents=True, exist_ok=True)

MAX_ATTEMPTS = 3

SOURCE_AUDIO_TYPES: set[SegmentSource] = {"mic", "system", "mixed"}

model_cache: dict[str, WhisperModel] = {}
merge_engine = TranscriptMergeEngine(overlap_policy="keep_both")


def _meeting_id_from_stem(file_stem: str) -> str:
    parts = file_stem.rsplit("_", 2)
    if len(parts) == 3:
        return parts[0]
    return file_stem


def _source_segment_files(meeting_id: str) -> dict[SegmentSource, list[Path]]:
    return {
        "mic": sorted(DONE.glob(f"{meeting_id}_mic_*.json"), key=lambda path: path.name),
        "system": sorted(DONE.glob(f"{meeting_id}_system_*.json"), key=lambda path: path.name),
        "mixed": sorted(DONE.glob(f"{meeting_id}_mixed_*.json"), key=lambda path: path.name),
    }


def _read_source_segments(segment_files: Iterable[Path], source: SegmentSource) -> list[dict]:
    normalized_segments: list[dict] = []
    default_speaker = DEFAULT_SPEAKER_BY_SOURCE[source]

    for segment_file in segment_files:
        try:
            data = json.loads(segment_file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[merge] Failed to parse {segment_file.name}: {exc}")
            continue

        for index, segment in enumerate(data.get("segments", [])):
            try:
                normalized = normalize_segment(
                    segment,
                    source=source,
                    default_speaker=default_speaker,
                    segment_index=index,
                )
            except Exception as exc:
                print(f"[merge] Invalid segment in {segment_file.name}: {exc}")
                continue

            if not normalized["text"]:
                continue
            normalized_segments.append(normalized)

    return normalized_segments


def _build_final_transcript(
    meeting_id: str,
    merged_segments: list[dict],
    complete: bool,
) -> dict:
    return {
        "meeting_id": meeting_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "complete": complete,
        "segment_count": len(merged_segments),
        "final_transcript": {
            "segments": merged_segments,
        },
        "segments": merged_segments,
    }


def check_and_combine_transcripts(meeting_id: str, finalize: bool = False) -> bool:
    pending_count = len(list(PENDING.glob(f"{meeting_id}_*_*.wav")))
    processing_count = len(list(PROCESSING.glob(f"{meeting_id}_*_*.wav")))

    if finalize and (pending_count > 0 or processing_count > 0):
        return False

    source_files = _source_segment_files(meeting_id)
    has_source_files = bool(source_files["mic"] or source_files["system"] or source_files["mixed"])

    if not has_source_files:
        return (DONE / f"{meeting_id}.json").exists()

    mic_segments = _read_source_segments(source_files["mic"], "mic")
    system_segments = _read_source_segments(source_files["system"], "system")
    mixed_segments = _read_source_segments(source_files["mixed"], "mixed")
    
    if mixed_segments:
        merged_segments = mixed_segments
    else:
        merged_segments = merge_engine.merge_segments(mic_segments, system_segments)

    complete = finalize and pending_count == 0 and processing_count == 0
    final_payload = _build_final_transcript(
        meeting_id=meeting_id,
        merged_segments=merged_segments,
        complete=complete,
    )

    output = DONE / f"{meeting_id}.json"
    output.write_text(json.dumps(final_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if complete:
        for source in SOURCE_AUDIO_TYPES:
            for file_path in source_files[source]:
                try:
                    file_path.unlink()
                except FileNotFoundError:
                    pass

    return True


import threading
_model_lock = threading.Lock()

def get_model(model_name: str = "large-v3"):
    with _model_lock:
        if model_name not in model_cache:
            device_info = detect_device()
            device = device_info["device"]
            compute_type = device_info["compute_type"]

            print(f"Loading model {model_name} on {device} ({compute_type})...")
            try:
                model_cache[model_name] = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                )
                print(f"Model {model_name} loaded on {device}!")
            except Exception as e:
                print(f"Failed to load model {model_name} on {device}: {e}. Falling back to CPU...")
                model_cache[model_name] = WhisperModel(
                    model_name,
                    device="cpu",
                    compute_type="int8",
                )
                print(f"Model {model_name} loaded on CPU!")
        return model_cache[model_name]


def transcribe_audio(audio_path: Path, model_name: str = "large-v3", audio_type: str = "mic"):
    model = get_model(model_name)

    try:
        if audio_type == "mic":
            return transcribe_mic_audio(model, audio_path)
        if audio_type == "system":
            return transcribe_system_audio(model, audio_path)
        if audio_type == "mixed":
            return transcribe_mic_audio(model, audio_path)
    except Exception as e:
        error_str = str(e).lower()
        if "cublas" in error_str or "cudnn" in error_str or "cuda" in error_str:
            print(f"CUDA error detected during transcription: {e}. Falling back to CPU...")
            with _model_lock:
                model_cache[model_name] = WhisperModel(
                    model_name,
                    device="cpu",
                    compute_type="int8",
                )
            model = model_cache[model_name]
            if audio_type == "mic":
                return transcribe_mic_audio(model, audio_path)
            if audio_type == "system":
                return transcribe_system_audio(model, audio_path)
            if audio_type == "mixed":
                return transcribe_mic_audio(model, audio_path)
        raise e

    print(f"[queue] Unsupported audio type '{audio_type}', skipping file {audio_path.name}")
    return {"segments": []}


def process_file(audio_file: Path, model_name: str = "large-v3"):
    audio_type = "mic"
    segment_index = 0
    attempts = 0

    meta_file = PENDING / f"{audio_file.stem}.meta.json"
    if not meta_file.exists():
        meta_file = PROCESSING / f"{audio_file.stem}.meta.json"
    if not meta_file.exists():
        meta_file = audio_file.with_suffix(".meta.json")

    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        audio_type = str(meta.get("audio_type", "mic"))
        segment_index = int(meta.get("segment_index", 0) or 0)
        attempts = int(meta.get("attempts", 0) or 0)

    meeting_id = _meeting_id_from_stem(audio_file.stem)

    if audio_type not in SOURCE_AUDIO_TYPES:
        try:
            audio_file.unlink()
        except FileNotFoundError:
            pass
        if meta_file.exists():
            meta_file.unlink()
        check_and_combine_transcripts(meeting_id, finalize=False)
        return True

    try:
        result = transcribe_audio(audio_file, model_name, audio_type)

        output_file = DONE / f"{meeting_id}_{audio_type}_{segment_index}.json"
        output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        audio_file.unlink()
        if meta_file.exists():
            meta_file.unlink()

        check_and_combine_transcripts(meeting_id, finalize=False)
        return True
    except Exception as exc:
        print(f"Error processing {audio_file}: {exc}")
        attempts += 1

        meta_data_file = audio_file.with_suffix(".meta.json")
        meta = {
            "audio_type": audio_type,
            "attempts": attempts,
            "max_attempts": MAX_ATTEMPTS,
            "segment_index": segment_index,
        }
        meta_data_file.write_text(json.dumps(meta), encoding="utf-8")

        if attempts >= MAX_ATTEMPTS:
            audio_file.replace(FAILED / audio_file.name)
            meta_data_file.replace(FAILED / meta_data_file.name)
        else:
            audio_file.replace(PENDING / audio_file.name)

        return False


def worker(worker_id: int, model_name: str = "large-v3", workers_count: int = 2):
    print(f"Worker {worker_id} started")

    while True:
        files = list(PENDING.glob("*.wav"))

        processed_meetings = set()

        for audio_file in files:
            meta_file = PENDING / f"{audio_file.stem}.meta.json"

            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
                if meta.get("attempts", 0) > (worker_id % MAX_ATTEMPTS):
                    continue

            dest_audio = PROCESSING / audio_file.name
            dest_meta = PROCESSING / f"{audio_file.stem}.meta.json"

            try:
                audio_file.rename(dest_audio)
                if meta_file.exists():
                    meta_file.rename(dest_meta)
            except Exception:
                # File was already taken by another worker
                continue

            print(f"Worker {worker_id} processing {audio_file.name}")
            success = process_file(dest_audio, model_name)

            if success:
                meeting_id = _meeting_id_from_stem(audio_file.stem)
                processed_meetings.add(meeting_id)

        for meeting_id in processed_meetings:
            pending_for_meeting = list(PENDING.glob(f"{meeting_id}_*_*.wav"))
            processing_for_meeting = list(PROCESSING.glob(f"{meeting_id}_*_*.wav"))

            if not pending_for_meeting and not processing_for_meeting:
                check_and_combine_transcripts(meeting_id, finalize=True)

        time.sleep(5)


def start_workers(workers_count: int = 2, model_name: str = "large-v3"):
    print("Executing startup recovery: moving stale processing files back to pending.")
    for stale_file in PROCESSING.glob("*.wav"):
        try:
            stale_file.replace(PENDING / stale_file.name)
            stale_meta = PROCESSING / f"{stale_file.stem}.meta.json"
            if stale_meta.exists():
                stale_meta.replace(PENDING / stale_meta.name)
        except Exception as exc:
            print(f"Failed to recover {stale_file.name}: {exc}")

    for i in range(workers_count):
        thread = Thread(target=worker, args=(i, model_name, workers_count), daemon=True)
        thread.start()
        print(f"Worker {i} started")


def get_queue_stats():
    return {
        "pending": len(list(PENDING.glob("*.wav"))),
        "processing": len(list(PROCESSING.glob("*.wav"))),
        "done": len(list(DONE.glob("meeting_*.json"))),
        "failed": len(list(FAILED.glob("*.json"))),
    }


if __name__ == "__main__":
    print("Queue worker starting...")
    start_workers(workers_count=2, model_name="large-v3")

    while True:
        time.sleep(60)
        print(f"Queue stats: {get_queue_stats()}")
