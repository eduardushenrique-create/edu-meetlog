import json
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Iterable

from gpu_detection import detect_device, _ensure_nvidia_dlls_on_path
# Must add NVIDIA DLL dirs to PATH *before* importing faster_whisper,
# because CTranslate2 tries to load cuBLAS at import time on Windows.
_ensure_nvidia_dlls_on_path()

from faster_whisper import WhisperModel

from transcription.merge_engine import TranscriptMergeEngine
from transcription.mic_worker import transcribe_mic_audio
from transcription.models import DEFAULT_SPEAKER_BY_SOURCE, SegmentSource, normalize_segment
from transcription.system_worker import transcribe_system_audio

from paths import QUEUE_DIR, CONFIG_DIR

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

_MEETINGS_FILE = CONFIG_DIR / "meetings.json"


def _persist_meeting_status(meeting_id: str, status: str) -> None:
    """Update the status of a meeting in meetings.json without importing main.py."""
    try:
        if not _MEETINGS_FILE.exists():
            return
        meetings = json.loads(_MEETINGS_FILE.read_text(encoding="utf-8"))
        changed = False
        for m in meetings:
            if m.get("id") == meeting_id and m.get("status") != status:
                m["status"] = status
                changed = True
                break
        if changed:
            _MEETINGS_FILE.write_text(json.dumps(meetings, indent=2), encoding="utf-8")
            print(f"[queue] Meeting {meeting_id} status persisted as '{status}'")
    except Exception as exc:
        print(f"[queue] WARNING: could not persist status for {meeting_id}: {exc}")

def _persist_meeting_suggested_labels(meeting_id: str, suggested_label_ids: list[str]) -> None:
    """Update the suggested_labels of a meeting in meetings.json without importing main.py."""
    try:
        if not _MEETINGS_FILE.exists():
            return
        meetings = json.loads(_MEETINGS_FILE.read_text(encoding="utf-8"))
        changed = False
        for m in meetings:
            if m.get("id") == meeting_id:
                m["suggested_labels"] = suggested_label_ids
                changed = True
                break
        if changed:
            _MEETINGS_FILE.write_text(json.dumps(meetings, indent=2), encoding="utf-8")
            print(f"[queue] Meeting {meeting_id} suggested labels persisted")
    except Exception as exc:
        print(f"[queue] WARNING: could not persist suggested labels for {meeting_id}: {exc}")


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

    print(f"[queue] check_and_combine_transcripts for {meeting_id} (finalize={finalize})")
    
    if finalize and (pending_count > 0 or processing_count > 0):
        print(f"[queue] finalize=True but files still exist: pending={pending_count}, processing={processing_count}")
        return False

    source_files = _source_segment_files(meeting_id)
    has_source_files = bool(source_files["mic"] or source_files["system"] or source_files["mixed"])

    if not has_source_files:
        print(f"[queue] No source files for {meeting_id}")
        return (DONE / f"{meeting_id}.json").exists()

    mic_segments = _read_source_segments(source_files["mic"], "mic")
    system_segments = _read_source_segments(source_files["system"], "system")
    mixed_segments = _read_source_segments(source_files["mixed"], "mixed")
    
    try:
        if mixed_segments:
            merged_segments = mixed_segments
        else:
            print(f"[queue] Merging {len(mic_segments)} mic segments and {len(system_segments)} system segments")
            merged_segments = merge_engine.merge_segments(mic_segments, system_segments)
    except Exception as e:
        print(f"[queue] CRITICAL ERROR merging segments for {meeting_id}: {e}")
        raise e

    complete = finalize and pending_count == 0 and processing_count == 0
    final_payload = _build_final_transcript(
        meeting_id=meeting_id,
        merged_segments=merged_segments,
        complete=complete,
    )

    # NOTE: Speaker assignment is already correct from the transcription step:
    #   mic  → speaker="user"   (transcribe_mic_audio)
    #   system → speaker="system" (transcribe_system_audio)
    # No post-hoc diarization is applied — the heuristic in diarization.py
    # (text-matching on "legenda"/"mic") would overwrite the correct values.


    output = DONE / f"{meeting_id}.json"
    content_str = json.dumps(final_payload, indent=2, ensure_ascii=False)
    output.write_text(content_str, encoding="utf-8")

    # If this is the final processing step, export a copy to the user's custom output folder
    if complete:
        from paths import get_transcripts_dir
        user_output = get_transcripts_dir() / f"{meeting_id}.json"
        try:
            user_output.write_text(content_str, encoding="utf-8")
        except Exception as e:
            print(f"[queue] Failed to save transcript to custom output folder: {e}")
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


def transcribe_audio(audio_path: Path, model_name: str = "large-v3", audio_type: str = "mic") -> dict:
    model = get_model(model_name)

    def _run(m):
        if audio_type in ("mic", "mixed"):
            return transcribe_mic_audio(m, audio_path)
        if audio_type == "system":
            return transcribe_system_audio(m, audio_path)
        print(f"[queue] Unsupported audio type '{audio_type}', skipping file {audio_path.name}")
        return {"segments": []}

    try:
        result = _run(model)
        return result if result is not None else {"segments": []}
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
            result = _run(model)
            return result if result is not None else {"segments": []}
        raise e


def process_file(audio_file: Path, model_name: str = "large-v3"):
    audio_type = "mic"
    segment_index = 0
    attempts = 0

    # Meta file was moved to PROCESSING by _pickup_next_file; check there first.
    meta_file = PROCESSING / f"{audio_file.stem}.meta.json"
    if not meta_file.exists():
        meta_file = PENDING / f"{audio_file.stem}.meta.json"
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
        print(f"[queue] Starting transcription for {audio_file.name} (type: {audio_type}, model: {model_name})")
        result = transcribe_audio(audio_file, model_name, audio_type)
        print(f"[queue] Transcription finished for {audio_file.name}. Got {len(result.get('segments', []))} segments.")

        output_file = DONE / f"{meeting_id}_{audio_type}_{segment_index}.json"
        print(f"[queue] Writing partial JSON to {output_file.name}")
        output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"[queue] Deleting processed WAV file {audio_file.name}")
        audio_file.unlink()
        if meta_file.exists():
            meta_file.unlink()

        print(f"[queue] Calling check_and_combine_transcripts for {meeting_id}")
        check_and_combine_transcripts(meeting_id, finalize=False)
        print(f"[queue] process_file completed successfully for {audio_file.name}")
        return True
    except Exception as exc:
        print(f"[queue] ERROR processing {audio_file}: {exc}")
        import traceback
        traceback.print_exc()
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
            if audio_file.exists():
                audio_file.replace(FAILED / audio_file.name)
            if meta_data_file.exists():
                meta_data_file.replace(FAILED / meta_data_file.name)
        else:
            if audio_file.exists():
                audio_file.replace(PENDING / audio_file.name)

        return False


# Files stuck in /processing/ longer than this are considered stale and recovered.
_STALE_PROCESSING_THRESHOLD_SECS = 600  # 10 minutes


def _recover_stale_processing_files():
    """Move WAV files stuck in /processing/ back to /pending/ so they are retried."""
    now = time.time()
    for stale_file in list(PROCESSING.glob("*.wav")):
        try:
            age = now - stale_file.stat().st_mtime
        except FileNotFoundError:
            continue
        if age >= _STALE_PROCESSING_THRESHOLD_SECS:
            print(f"[queue] Recovering stale file ({age:.0f}s old): {stale_file.name}")
            try:
                stale_file.replace(PENDING / stale_file.name)
                stale_meta = PROCESSING / f"{stale_file.stem}.meta.json"
                if stale_meta.exists():
                    stale_meta.replace(PENDING / stale_meta.name)
            except Exception as exc:
                print(f"[queue] Failed to recover stale file {stale_file.name}: {exc}")

# Lock to serialize file pickup across workers — prevents two workers
# from globbing the same pending list and both renaming the same file.
import threading as _threading
_pickup_lock = _threading.Lock()


def _pickup_next_file() -> tuple[Path, dict] | None:
    """Atomically pick the next pending WAV file and move it to processing.

    Files are sorted by (priority ASC, mtime ASC) so lower-priority numbers
    (e.g. 0 = realtime) are always processed before higher ones (1 = batch).

    Returns (processing_path, meta_dict) or None if no files available.
    """
    with _pickup_lock:
        files = list(PENDING.glob("*.wav"))
        if not files:
            return None

        # Read priorities from meta files, defaulting to batch priority (1)
        def _file_priority(f: Path) -> tuple[int, float]:
            meta_f = PENDING / (f.stem + ".meta.json")
            priority = 1  # default: batch
            if meta_f.exists():
                try:
                    m = json.loads(meta_f.read_text(encoding="utf-8"))
                    priority = int(m.get("priority", 1))
                except Exception:
                    pass
            try:
                mtime = f.stat().st_mtime
            except OSError:
                mtime = 0.0
            return (priority, mtime)

        files.sort(key=_file_priority)
        audio_file = files[0]

        meta_file = PENDING / (audio_file.stem + ".meta.json")
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        dest_audio = PROCESSING / audio_file.name
        dest_meta  = PROCESSING / (audio_file.stem + ".meta.json")

        try:
            audio_file.rename(dest_audio)
            if meta_file.exists():
                meta_file.rename(dest_meta)
        except Exception:
            return None

        return dest_audio, meta


def worker(worker_id: int, model_name: str = "large-v3", workers_count: int = 2):
    print(f"Worker {worker_id} ready")

    while True:
        # Only worker 0 runs the stale-file recovery to avoid races.
        if worker_id == 0:
            _recover_stale_processing_files()

        pickup = _pickup_next_file()
        if pickup is None:
            time.sleep(5)
            continue

        dest_audio, meta = pickup
        original_name = dest_audio.name

        print(f"Worker {worker_id} picked up {original_name}")
        success = process_file(dest_audio, model_name)

        if success:
            print(f"Worker {worker_id} successfully processed {original_name}")
            meeting_id = _meeting_id_from_stem(dest_audio.stem)

            pending_for_meeting = list(PENDING.glob(meeting_id + "_*_*.wav"))
            processing_for_meeting = list(PROCESSING.glob(meeting_id + "_*_*.wav"))

            if not pending_for_meeting and not processing_for_meeting:
                print(f"Worker {worker_id}: Meeting {meeting_id} is completely processed! Finalizing...")
                ok = check_and_combine_transcripts(meeting_id, finalize=True)
                if ok:
                    _persist_meeting_status(meeting_id, "done")
                    
                    # Generate automatic label suggestions (F3.2.8)
                    try:
                        import sys, os
                        if str(Path(__file__).parent) not in sys.path:
                            sys.path.insert(0, str(Path(__file__).parent))
                        from ai_engine import suggest_labels
                        
                        labels_file = CONFIG_DIR / "labels.json"
                        if labels_file.exists():
                            available_labels = json.loads(labels_file.read_text(encoding="utf-8"))
                            transcript_path = DONE / f"{meeting_id}.json"
                            if transcript_path.exists() and available_labels:
                                data = json.loads(transcript_path.read_text(encoding="utf-8"))
                                full_text = " ".join([s.get("text", "") for s in data.get("segments", [])])
                                if full_text:
                                    suggested_ids = suggest_labels(full_text, available_labels)
                                    if suggested_ids:
                                        _persist_meeting_suggested_labels(meeting_id, suggested_ids)
                    except Exception as exc:
                        print(f"Worker {worker_id}: Failed to generate automatic label suggestions: {exc}")
            else:
                print(f"Worker {worker_id}: Meeting {meeting_id} still has pending/processing files. Waiting.")

        # Small delay before picking the next file
        time.sleep(1)


# Maximum number of concurrent workers regardless of user setting.
# large-v3 on GPU uses ~3 GB VRAM.  The model is SHARED (model_cache) so extra
# workers only add threading lock contention — they never speed up transcription.
# 2 workers is the sweet spot: one processes while the other picks the next file.
_MAX_EFFECTIVE_WORKERS = 2


def start_workers(workers_count: int = 2, model_name: str = "large-v3"):
    print("Executing startup recovery: moving stale processing files back to pending.")
    for stale_file in list(PROCESSING.glob("*.wav")):
        try:
            stale_file.replace(PENDING / stale_file.name)
            stale_meta = PROCESSING / f"{stale_file.stem}.meta.json"
            if stale_meta.exists():
                stale_meta.replace(PENDING / stale_meta.name)
        except Exception as exc:
            print(f"Failed to recover {stale_file.name}: {exc}")

    # Cap workers: sharing 1 model instance means extra workers only block on
    # the model lock — they don't add throughput and make the first job appear
    # hung until all locks are resolved.
    effective_workers = min(workers_count, _MAX_EFFECTIVE_WORKERS)
    if workers_count > effective_workers:
        print(
            f"[queue] Capping workers from {workers_count} to {effective_workers} "
            f"(model '{model_name}' is shared — extra workers only add lock contention)"
        )

    # Pre-warm the model BEFORE spawning threads so workers don't race to load it.
    print(f"[queue] Pre-warming model '{model_name}' before starting workers...")
    try:
        get_model(model_name)
        print(f"[queue] Model '{model_name}' ready.")
    except Exception as exc:
        print(f"[queue] WARNING: model pre-warm failed: {exc}")

    for i in range(effective_workers):
        thread = Thread(target=worker, args=(i, model_name, effective_workers), daemon=True)
        thread.start()
        print(f"[queue] Worker {i} started")


def get_queue_stats():
    return {
        "pending": len(list(PENDING.glob("*.wav"))),
        "processing": len(list(PROCESSING.glob("*.wav"))),
        "done": len(list(DONE.glob("meeting_*.json"))),
        "failed": len(list(FAILED.glob("*.wav"))),
    }


if __name__ == "__main__":
    print("Queue worker starting...")
    start_workers(workers_count=2, model_name="large-v3")

    while True:
        time.sleep(60)
        print(f"Queue stats: {get_queue_stats()}")
