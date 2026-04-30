import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import shutil
import time
import threading
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
from pathlib import Path

from audio_capture import AudioCapture, SAMPLE_RATE
from queue_worker import check_and_combine_transcripts, start_workers as start_queue_workers
from gpu_detection import detect_device
from meeting_detection import MeetingDetector, ProcessMonitor
from diarization import DiarizationEngine, align_speakers_to_transcript
from realtime_transcriber import RealtimeTranscriber
from transcription.merge_engine import TranscriptMergeEngine
from audit_log import log_audit_event

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.loop = asyncio.get_running_loop()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_transcription(self, data: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

    def send_transcription_from_thread(self, data: dict):
        if not self.active_connections or self.loop is None:
            return
        future = asyncio.run_coroutine_threadsafe(self.send_transcription(data), self.loop)
        try:
            future.result(timeout=2)
        except Exception:
            pass

manager = ConnectionManager()
capture = AudioCapture()

from paths import (
    ACTION_ITEMS_FILE,
    CLIENTS_FILE,
    CONFIG_DIR,
    LABELS_FILE,
    PEOPLE_FILE,
    RECORDINGS_DIR,
    QUEUE_DIR,
    STAKEHOLDERS_FILE,
    TRANSCRIPTS_DIR,
)

MEETINGS_FILE = CONFIG_DIR / "meetings.json"

(QUEUE_DIR / "pending").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "processing").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "done").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "failed").mkdir(parents=True, exist_ok=True)

app_state = {
    "state": "IDLE",
    "session_start": None,
    "recording_duration": 0,
    "current_meeting_id": None,
    "mic_enabled": True,
    "system_enabled": False,
}

# Models
class Label(BaseModel):
    id: str
    name: str
    color: str

class MeetingLabelsUpdate(BaseModel):
    label_ids: list[str]

class BulkActionRequest(BaseModel):
    ids: list[str]

class MeetingClassificationUpdate(BaseModel):
    client_id: Optional[str] = None
    meeting_kind: Optional[str] = None

class RecordingRequest(BaseModel):
    mic_enabled: bool = True
    system_enabled: bool = False
    segment_duration: int = 300

class PopupRequest(BaseModel):
    popup_type: str = "info"
    title: str
    message: str
    buttons: list[str] = []

class Settings(BaseModel):
    mic_enabled: bool = True
    system_enabled: bool = False
    model: str = "large-v3"
    workers: int = 2
    auto_start: bool = False
    output_folder: str = ""

class ClientCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    labels: list[str] = Field(default_factory=list)
    active: bool = True

class PersonCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    email: str = ""
    aliases: list[str] = Field(default_factory=list)
    notes: str = ""
    labels: list[str] = Field(default_factory=list)
    client_ids: list[str] = Field(default_factory=list)
    is_temporary: bool = False
    voice_profile_id: Optional[str] = None

class StakeholderCreateRequest(BaseModel):
    id: Optional[str] = None
    client_id: str
    person_id: str
    role: str
    influence_level: str = "unknown"
    notes: str = ""
    labels: list[str] = Field(default_factory=list)
    is_primary: bool = False

class ActionItemEvidenceRequest(BaseModel):
    meeting_id: Optional[str] = None
    segment_id: Optional[str] = None
    excerpt: str = ""
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    source: str = "manual"

class ActionItemCreateRequest(BaseModel):
    id: Optional[str] = None
    title: str
    client_id: Optional[str] = None
    meeting_id: Optional[str] = None
    assignee_person_id: Optional[str] = None
    suggested_assignee_person_id: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    due_date: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    notes: str = ""
    evidence: list[ActionItemEvidenceRequest] = Field(default_factory=list)
    source: str = "manual"

# Detection Hooks
def _on_meeting_start():
    print("[main] Meeting start detected — sending popup.")
    manager.send_transcription_from_thread({
        "type": "popup",
        "action": "start",
        "title": "Reunião detectada",
        "message": "Uma reunião foi detectada. Deseja iniciar a gravação?",
    })

def _on_meeting_end():
    print("[main] Meeting end detected — sending popup.")
    if app_state.get("state") == "RECORDING":
        manager.send_transcription_from_thread({
            "type": "popup",
            "action": "stop",
            "title": "Reunião finalizada?",
            "message": "Parece que a reunião terminou. Deseja parar a gravação?",
        })

meeting_detector = MeetingDetector(on_start=_on_meeting_start, on_end=_on_meeting_end)
process_monitor = ProcessMonitor()
process_monitor.start()

@app.on_event("startup")
async def on_startup():
    scan_output_folder_for_meetings()
    meeting_detector.start()

# Real-time pipeline
realtime_transcriber = None
realtime_merge_engine = TranscriptMergeEngine(overlap_policy="keep_both")
realtime_thread = None
realtime_running = False
realtime_meeting_id = None
realtime_offsets = {"mic": 0.0, "system": 0.0}
realtime_session_start = None
realtime_lock = threading.Lock()

def _broadcast_transcription_from_thread(payload: dict):
    manager.send_transcription_from_thread(payload)

def _process_realtime_source_chunks(meeting_id: str, source: str, chunks: list):
    global realtime_offsets
    global realtime_transcriber

    if realtime_transcriber is None:
        return

    speaker = "user" if source == "mic" else "system"

    for chunk_item in chunks:
        chunk_start_time = None
        chunk = chunk_item
        if isinstance(chunk_item, tuple) and len(chunk_item) == 2:
            chunk_start_time, chunk = chunk_item

        if chunk is None or len(chunk) == 0:
            continue

        if chunk_start_time is not None and realtime_session_start is not None:
            offset = max(0.0, float(chunk_start_time) - float(realtime_session_start))
            realtime_offsets[source] = max(
                realtime_offsets[source],
                offset + float(len(chunk)) / float(SAMPLE_RATE),
            )
        else:
            offset = realtime_offsets[source]
            realtime_offsets[source] += float(len(chunk)) / float(SAMPLE_RATE)

        segments = realtime_transcriber.transcribe_chunk(
            chunk,
            source=source,
            speaker=speaker,
            time_offset=offset,
        )
        if not segments:
            continue

        merge_result = realtime_merge_engine.merge_incremental(meeting_id, source, segments)
        if not merge_result.new_segments:
            continue

        _broadcast_transcription_from_thread({
            "meeting_id": meeting_id,
            "is_partial": True,
            "segments": merge_result.new_segments,
            "final_transcript": {
                "segments": merge_result.merged_segments,
            },
        })

def _realtime_worker_loop(meeting_id: str):
    global realtime_running
    while realtime_running and app_state.get("current_meeting_id") == meeting_id:
        if app_state.get("state") == "PAUSED":
            time.sleep(0.2)
            continue
        chunks = capture.get_realtime_chunks()
        mic_chunks = chunks.get("mic", [])
        system_chunks = chunks.get("system", [])
        for chunk_item in mic_chunks:
            chunk = chunk_item[1] if isinstance(chunk_item, tuple) and len(chunk_item) == 2 else chunk_item
            if chunk is not None and len(chunk) > 0:
                meeting_detector.feed_audio(chunk)
        _process_realtime_source_chunks(meeting_id, "mic", mic_chunks)
        _process_realtime_source_chunks(meeting_id, "system", system_chunks)
        time.sleep(0.2)

def start_realtime_pipeline(meeting_id: str, model_name: str):
    global realtime_running, realtime_meeting_id, realtime_thread, realtime_offsets, realtime_session_start, realtime_transcriber
    stop_realtime_pipeline()
    with realtime_lock:
        realtime_running = True
        realtime_meeting_id = meeting_id
        realtime_offsets = {"mic": 0.0, "system": 0.0}
        realtime_session_start = app_state.get("session_start") or time.time()
    realtime_merge_engine.clear_stream(meeting_id)
    if realtime_transcriber is None or realtime_transcriber.model_name != model_name:
        realtime_transcriber = RealtimeTranscriber(model_name=model_name)
    realtime_transcriber.start()
    realtime_thread = threading.Thread(target=_realtime_worker_loop, args=(meeting_id,), daemon=True)
    realtime_thread.start()

def stop_realtime_pipeline():
    global realtime_running, realtime_meeting_id, realtime_thread, realtime_transcriber, realtime_session_start
    with realtime_lock:
        meeting_id = realtime_meeting_id
        realtime_running = False
        realtime_meeting_id = None
        realtime_session_start = None
    if realtime_thread and realtime_thread.is_alive():
        realtime_thread.join(timeout=1.0)
    realtime_thread = None
    if realtime_transcriber is not None:
        realtime_transcriber.stop()
    capture.mic_chunk_buffer.clear()
    capture.system_chunk_buffer.clear()
    if meeting_id:
        realtime_merge_engine.clear_stream(meeting_id)

# Helpers
def scan_output_folder_for_meetings():
    from paths import get_transcripts_dir, QUEUE_DIR as _QUEUE_DIR
    transcripts_dir = get_transcripts_dir()
    done_dir = _QUEUE_DIR / "done"
    for scan_dir in [transcripts_dir, done_dir]:
        if not scan_dir.exists(): continue
        for jf in scan_dir.glob("meeting_*.json"):
            if any(x in jf.stem for x in ["_mic_", "_system_", "_mixed_"]): continue
            meeting_id = jf.stem
            if any(m["id"] == meeting_id for m in load_meetings()): continue
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                segments = data.get("final_transcript", {}).get("segments", data.get("segments", []))
                duration_secs = segments[-1]["end"] if segments else 0
                add_meeting({
                    "id": meeting_id,
                    "name": data.get("name", f"Reunião importada"),
                    "date": data.get("date", jf.stat().st_mtime),
                    "duration": format_duration(duration_secs),
                    "status": "done",
                    "segments": len(segments),
                })
            except: pass

def load_settings():
    settings_file = CONFIG_DIR / "settings.json"
    if settings_file.exists(): return json.loads(settings_file.read_text())
    return {"mic_enabled": True, "system_enabled": False, "model": "large-v3", "workers": 2, "auto_start": False, "output_folder": ""}

def save_settings(settings: dict):
    settings_file = CONFIG_DIR / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2))
    import paths as _paths
    _paths.TRANSCRIPTS_DIR = _paths.get_transcripts_dir()
    scan_output_folder_for_meetings()

def load_meetings():
    if MEETINGS_FILE.exists(): return json.loads(MEETINGS_FILE.read_text())
    return []

def save_meetings(meetings: list):
    MEETINGS_FILE.write_text(json.dumps(meetings, indent=2))

def load_labels():
    if LABELS_FILE.exists():
        try: return json.loads(LABELS_FILE.read_text(encoding="utf-8"))
        except: return []
    return []

def save_labels(labels: list):
    LABELS_FILE.write_text(json.dumps(labels, indent=2, ensure_ascii=False), encoding="utf-8")

def _load_json_list(file_path: Path) -> list:
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_json_list(file_path: Path, items: list):
    file_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

def load_clients():
    return _load_json_list(CLIENTS_FILE)

def save_clients(clients: list):
    _save_json_list(CLIENTS_FILE, clients)

def load_people():
    return _load_json_list(PEOPLE_FILE)

def save_people(people: list):
    _save_json_list(PEOPLE_FILE, people)

def load_stakeholders():
    return _load_json_list(STAKEHOLDERS_FILE)

def save_stakeholders(stakeholders: list):
    _save_json_list(STAKEHOLDERS_FILE, stakeholders)

def load_action_items():
    return _load_json_list(ACTION_ITEMS_FILE)

def save_action_items(action_items: list):
    _save_json_list(ACTION_ITEMS_FILE, action_items)

def utc_now_iso() -> str:
    return datetime.now().isoformat()

def find_or_404(items: list, item_id: str, label: str):
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return item

def parse_duration_to_minutes(raw_duration) -> float:
    if raw_duration is None:
        return 0.0
    if isinstance(raw_duration, (int, float)):
        return round(float(raw_duration) / 60.0, 2)

    text = str(raw_duration).strip()
    if not text:
        return 0.0

    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = [int(part) for part in parts]
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = [int(part) for part in parts]
            total_seconds = minutes * 60 + seconds
        else:
            total_seconds = float(text)
    except ValueError:
        return 0.0

    return round(float(total_seconds) / 60.0, 2)

def parse_meeting_datetime(raw_value) -> Optional[datetime]:
    if raw_value is None:
        return None

    if isinstance(raw_value, (int, float)):
        try:
            return datetime.fromtimestamp(raw_value)
        except Exception:
            return None

    text = str(raw_value).strip()
    if not text:
        return None

    for candidate in (text.replace("Z", "+00:00"), text):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue

    try:
        return datetime.fromtimestamp(float(text))
    except Exception:
        return None

def calculate_client_indicators(client_id: str, reference_date: Optional[str] = None) -> dict:
    meetings = [meeting for meeting in load_meetings() if meeting.get("client_id") == client_id and not meeting.get("archived", False)]
    reference_dt = parse_meeting_datetime(reference_date) or datetime.now()

    weekly_total = 0.0
    monthly_total = 0.0
    weekly_external = 0.0
    weekly_internal = 0.0
    monthly_external = 0.0
    monthly_internal = 0.0
    counted_weekly_ids = []
    counted_monthly_ids = []

    for meeting in meetings:
        meeting_dt = parse_meeting_datetime(meeting.get("meeting_at") or meeting.get("date"))
        if meeting_dt is None:
            continue

        duration_minutes = parse_duration_to_minutes(meeting.get("duration"))
        if duration_minutes <= 0:
            continue

        same_iso_week = meeting_dt.isocalendar()[:2] == reference_dt.isocalendar()[:2]
        same_month = meeting_dt.year == reference_dt.year and meeting_dt.month == reference_dt.month
        meeting_kind = meeting.get("meeting_kind", "external")

        if same_iso_week:
            weekly_total += duration_minutes
            counted_weekly_ids.append(meeting["id"])
            if meeting_kind == "internal":
                weekly_internal += duration_minutes
            else:
                weekly_external += duration_minutes

        if same_month:
            monthly_total += duration_minutes
            counted_monthly_ids.append(meeting["id"])
            if meeting_kind == "internal":
                monthly_internal += duration_minutes
            else:
                monthly_external += duration_minutes

    action_items = [item for item in load_action_items() if item.get("client_id") == client_id]
    open_action_items = [item for item in action_items if item.get("status") not in {"done", "cancelled"}]

    return {
        "client_id": client_id,
        "reference_date": reference_dt.date().isoformat(),
        "weekly_minutes": round(weekly_total, 2),
        "monthly_minutes": round(monthly_total, 2),
        "weekly_external_minutes": round(weekly_external, 2),
        "weekly_internal_minutes": round(weekly_internal, 2),
        "monthly_external_minutes": round(monthly_external, 2),
        "monthly_internal_minutes": round(monthly_internal, 2),
        "meeting_count": len(meetings),
        "weekly_meeting_ids": counted_weekly_ids,
        "monthly_meeting_ids": counted_monthly_ids,
        "open_action_items": len(open_action_items),
        "total_action_items": len(action_items),
    }

def add_meeting(meeting: dict):
    meetings = load_meetings()
    existing = next((m for m in meetings if m["id"] == meeting["id"]), None)
    if existing:
        existing.update(meeting)
    else:
        meeting.setdefault("labels", [])
        meeting.setdefault("archived", False)
        meeting.setdefault("client_id", None)
        meeting.setdefault("meeting_kind", None)
        meetings.insert(0, meeting)
    save_meetings(meetings)

def update_meeting_status(meeting_id: str, status: str):
    meetings = load_meetings()
    for m in meetings:
        if m["id"] == meeting_id:
            m["status"] = status
            break
    save_meetings(meetings)

def get_queue_stats():
    pending = set()
    for f in (QUEUE_DIR / "pending").glob("meeting_*_*_*.wav"):
        parts = f.stem.rsplit("_", 2)
        if len(parts) == 3: pending.add(parts[0])
    processing = set()
    for f in (QUEUE_DIR / "processing").glob("meeting_*_*_*.wav"):
        parts = f.stem.rsplit("_", 2)
        if len(parts) == 3: processing.add(parts[0])
    done = set()
    for f in (QUEUE_DIR / "done").glob("meeting_*.json"):
        if not any(x in f.stem for x in ["_mic_", "_system_", "_mixed_"]): done.add(f.stem)
    failed = set()
    for f in (QUEUE_DIR / "failed").glob("meeting_*.wav"):
        stem = f.stem
        if any(x in stem for x in ["_mic_", "_system_", "_mixed_"]): failed.add(stem.rsplit("_", 2)[0])
        else: failed.add(stem)
    return {"pending": len(pending - processing), "processing": len(processing), "done": len(done), "failed": len(failed)}

def move_to_queue(audio_path: Path, meeting_id: str, audio_type: str = "mic", segment_index: int = 0, priority: int = 1):
    dest = QUEUE_DIR / "pending" / f"{meeting_id}_{audio_type}_{segment_index}.wav"
    meta_dest = QUEUE_DIR / "pending" / f"{meeting_id}_{audio_type}_{segment_index}.meta.json"
    try:
        if dest.exists(): dest.unlink()
        shutil.copy(str(audio_path), str(dest))
        meta_dest.write_text(json.dumps({"audio_type": audio_type, "attempts": 0, "segment_index": segment_index, "priority": priority}))
    except: pass

def start_queue_workers_on_boot(settings: dict):
    start_queue_workers(settings.get("workers", 2), settings.get("model", "large-v3"))

def finalize_current_recording():
    global app_state
    meeting_id = app_state.get("current_meeting_id")
    result = capture.stop()
    stop_realtime_pipeline()
    duration = result.get("duration", 0)
    if result["success"]:
        app_state["state"] = "IDLE"
        app_state["recording_duration"] = duration
        if meeting_id and duration > 0:
            session_start = app_state.get("session_start")
            if session_start:
                session_files = [f for f in RECORDINGS_DIR.glob("*.wav") if f.stat().st_size > 0 and f.stat().st_mtime >= session_start]
            else:
                session_start_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                session_files = [f for f in RECORDINGS_DIR.glob("*.wav") if f.stat().st_size > 0 and session_start_time in f.stem]
            session_files = sorted(session_files, key=lambda f: f.stat().st_mtime)
            if session_files:
                segments_by_time = {}
                for wav_file in session_files:
                    parts = wav_file.stem.rsplit("_", 1)
                    if len(parts) == 2 and parts[1] in ("mic", "system", "mixed"):
                        segments_by_time.setdefault(parts[0], []).append((wav_file, parts[1]))
                if segments_by_time:
                    date_str = datetime.now().strftime("%d %b, %H:%M")
                    add_meeting({"id": meeting_id, "name": f"Reuniao {date_str}", "date": date_str, "duration": format_duration(duration), "status": "pending", "segments": len(segments_by_time), "wav_file": ", ".join([f.name for f in session_files])})
                    for idx, (_, files) in enumerate(sorted(segments_by_time.items())):
                        for wav_file, audio_type in files:
                            move_to_queue(wav_file, meeting_id, audio_type, idx)
                    update_meeting_status(meeting_id, "pending")
        app_state.update({"current_meeting_id": None, "recording_duration": 0, "session_start": None})
    return {"success": result["success"], "message": result["message"], "duration": duration, "meeting_id": meeting_id}

def format_duration(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"

# Endpoints
@app.post("/recording/start")
def start_recording(req: RecordingRequest):
    global app_state
    if app_state["state"] == "RECORDING": raise HTTPException(status_code=400, detail="Already recording")
    capture.mic_enabled, capture.system_enabled = req.mic_enabled, req.system_enabled
    result = capture.start()
    if result["success"]:
        app_state.update({"state": "RECORDING", "mic_enabled": req.mic_enabled, "system_enabled": req.system_enabled, "session_start": time.time(), "current_meeting_id": f"meeting_{uuid.uuid4().hex[:8]}", "recording_duration": 0})
        start_realtime_pipeline(meeting_id=app_state["current_meeting_id"], model_name=load_settings().get("model", "large-v3"))
    return {"success": result["success"], "message": result["message"], "meeting_id": app_state["current_meeting_id"]}

@app.post("/recording/pause")
def pause_recording():
    if app_state["state"] != "RECORDING": raise HTTPException(status_code=400, detail="Not recording")
    result = capture.pause()
    if result["success"]: app_state["state"] = "PAUSED"
    return result

@app.post("/recording/resume")
def resume_recording():
    if app_state["state"] != "PAUSED": raise HTTPException(status_code=400, detail="Not paused")
    result = capture.resume()
    if result["success"]: app_state["state"] = "RECORDING"
    return result

@app.post("/recording/finalize")
@app.post("/recording/stop")
def stop_recording():
    if app_state["state"] not in ["RECORDING", "PAUSED"]: raise HTTPException(status_code=400, detail="Not recording")
    return finalize_current_recording()

@app.get("/status")
def get_status():
    if app_state["state"] == "RECORDING" and app_state["session_start"]:
        app_state["recording_duration"] = time.time() - app_state["session_start"]
    device_info = detect_device()
    return {"state": app_state["state"], "recording_duration": app_state["recording_duration"], "mic_enabled": app_state["mic_enabled"], "system_enabled": app_state["system_enabled"], "queue_stats": get_queue_stats(), "settings": load_settings(), "meeting_id": app_state.get("current_meeting_id"), "gpu": {"available": device_info["cuda_available"], "device": device_info["device"], "compute_type": device_info["compute_type"], "gpu_info": device_info["gpu_info"]}}

@app.get("/meetings")
def get_meetings():
    meetings, changed = load_meetings(), False
    for m in meetings:
        meeting_id = m['id']
        wav_proc = any((QUEUE_DIR / "processing").glob(f"{meeting_id}_*_*.wav"))
        wav_exists = any((QUEUE_DIR / "pending").glob(f"{meeting_id}_*_*.wav"))
        json_done = (QUEUE_DIR / "done" / f"{meeting_id}.json").exists()
        json_failed = any((QUEUE_DIR / "failed").glob(f"{meeting_id}_*_*.wav"))
        new_status = "processing" if wav_proc else "pending" if wav_exists else "done" if json_done else "failed" if json_failed else m.get("status", "pending")
        if m.get("status") != new_status:
            m["status"], changed = new_status, True
    if changed: save_meetings(meetings)
    return sorted(meetings, key=lambda m: str(m.get("date", "")), reverse=True)

@app.get("/transcripts/{meeting_id}")
def get_transcript(meeting_id: str):
    for search_dir in [QUEUE_DIR / "done", TRANSCRIPTS_DIR]:
        f = search_dir / f"{meeting_id}.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            data.setdefault("meeting_id", meeting_id)
            data.setdefault("final_transcript", {"segments": data.get("segments", [])})
            data.setdefault("segments", data["final_transcript"].get("segments", []))
            return data
        for sf in search_dir.glob(f"{meeting_id}_*_*.json"):
            data = json.loads(sf.read_text(encoding="utf-8"))
            segs = data.get("segments", [])
            return {"meeting_id": meeting_id, "final_transcript": {"segments": segs}, "segments": segs}
    if check_and_combine_transcripts(meeting_id, finalize=False):
        f = QUEUE_DIR / "done" / f"{meeting_id}.json"
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            data.setdefault("meeting_id", meeting_id)
            data.setdefault("final_transcript", {"segments": data.get("segments", [])})
            data.setdefault("segments", data["final_transcript"].get("segments", []))
            return data
    raise HTTPException(status_code=404, detail="Transcript not found")

@app.post("/settings")
def update_settings(settings: Settings):
    save_settings(settings.dict())
    return {"success": True, "message": "Settings saved"}

@app.get("/settings")
def get_settings():
    return load_settings()

@app.get("/detection/status")
def get_detection_status():
    return {"meeting_active": meeting_detector.is_meeting_active, "active_apps": list(process_monitor.get_active_meeting_apps()), "vad_enabled": meeting_detector.running}

@app.post("/transcripts/{meeting_id}/diarize")
def diarize_transcript(meeting_id: str):
    f = QUEUE_DIR / "done" / f"{meeting_id}.json"
    if not f.exists(): raise HTTPException(status_code=404, detail="Transcript not found")
    data = json.loads(f.read_text(encoding="utf-8"))
    aligned = align_speakers_to_transcript(data.get("segments", []), {}, {})
    data["segments"] = data["final_transcript"] = {"segments": aligned}
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"success": True, "segments": aligned}

@app.post("/popup/show")
def show_popup(req: PopupRequest):
    return {"success": True, "id": f"popup_{int(time.time())}"}

@app.get("/labels")
def get_labels():
    return load_labels()

@app.post("/labels")
def create_label(label: Label):
    labels = load_labels()
    labels.append(label.dict())
    save_labels(labels)
    log_audit_event("CREATE_LABEL", {"label_id": label.id, "name": label.name})
    return {"success": True}

@app.delete("/labels/{label_id}")
def delete_label(label_id: str):
    save_labels([l for l in load_labels() if l["id"] != label_id])
    log_audit_event("DELETE_LABEL", {"label_id": label_id})
    return {"success": True}

@app.post("/meetings/{meeting_id}/labels")
def update_meeting_labels(meeting_id: str, update: MeetingLabelsUpdate):
    meetings = load_meetings()
    for m in meetings:
        if m["id"] == meeting_id:
            m["labels"] = update.label_ids
            break
    save_meetings(meetings)
    log_audit_event("UPDATE_MEETING_LABELS", {"meeting_id": meeting_id, "labels": update.label_ids})
    return {"success": True}

@app.post("/meetings/{meeting_id}/classification")
def classify_meeting(meeting_id: str, update: MeetingClassificationUpdate):
    meetings = load_meetings()
    meeting = next((item for item in meetings if item["id"] == meeting_id), None)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if "client_id" in update.__fields_set__ and update.client_id:
        find_or_404(load_clients(), update.client_id, "Client")
        meeting["client_id"] = update.client_id
    elif "client_id" in update.__fields_set__ and update.client_id is None:
        meeting["client_id"] = None

    if "meeting_kind" in update.__fields_set__:
        if update.meeting_kind not in {"internal", "external", ""}:
            raise HTTPException(status_code=400, detail="meeting_kind must be internal or external")
        meeting["meeting_kind"] = update.meeting_kind or None

    save_meetings(meetings)
    log_audit_event(
        "CLASSIFY_MEETING",
        {"meeting_id": meeting_id, "client_id": meeting.get("client_id"), "meeting_kind": meeting.get("meeting_kind")},
    )
    return {"success": True, "meeting": meeting}

@app.post("/meetings/bulk-delete")
def bulk_delete_meetings(req: BulkActionRequest):
    meetings, to_delete = load_meetings(), set(req.ids)
    for mid in to_delete:
        for d in ["pending", "processing", "done", "failed"]:
            for f in (QUEUE_DIR / d).glob(f"{mid}*"):
                try: f.unlink()
                except: pass
        for f in TRANSCRIPTS_DIR.glob(f"{mid}*"):
            try: f.unlink()
            except: pass
    save_meetings([m for m in meetings if m["id"] not in to_delete])
    log_audit_event("BULK_DELETE_MEETINGS", {"count": len(to_delete), "meeting_ids": list(to_delete)})
    return {"success": True, "deleted": len(to_delete)}

@app.post("/meetings/bulk-archive")
def bulk_archive_meetings(req: BulkActionRequest):
    meetings, to_archive = load_meetings(), set(req.ids)
    for m in meetings:
        if m["id"] in to_archive: m["archived"] = True
    save_meetings(meetings)
    log_audit_event("BULK_ARCHIVE_MEETINGS", {"count": len(to_archive), "meeting_ids": list(to_archive)})
    return {"success": True, "archived": len(to_archive)}

@app.post("/meetings/{meeting_id}/suggest-labels")
def suggest_meeting_labels(meeting_id: str):
    from ai_engine import suggest_labels as run_suggest
    
    # Try to load the transcript
    transcript = None
    try:
        transcript = get_transcript(meeting_id)
    except:
        raise HTTPException(status_code=404, detail="Transcript not found for suggestion")
        
    # Extract full text
    segments = transcript.get("segments", [])
    full_text = " ".join([s.get("text", "") for s in segments])
    
    if not full_text:
        return {"suggested_label_ids": []}
        
    available_labels = load_labels()
    suggested_ids = run_suggest(full_text, available_labels)
    
    return {"suggested_label_ids": suggested_ids}

@app.get("/clients")
def get_clients():
    return load_clients()

@app.post("/clients")
def create_client(payload: ClientCreateRequest):
    clients = load_clients()
    client_id = payload.id or f"client_{uuid.uuid4().hex[:8]}"
    if any(client.get("id") == client_id for client in clients):
        raise HTTPException(status_code=409, detail="Client id already exists")

    timestamp = utc_now_iso()
    client = {
        "id": client_id,
        "name": payload.name,
        "aliases": payload.aliases,
        "description": payload.description,
        "labels": payload.labels,
        "active": payload.active,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    clients.append(client)
    save_clients(clients)
    log_audit_event("CREATE_CLIENT", {"client_id": client_id, "name": payload.name})
    return {"success": True, "client": client}

@app.get("/clients/{client_id}")
def get_client(client_id: str):
    client = find_or_404(load_clients(), client_id, "Client")
    stakeholders = [item for item in load_stakeholders() if item.get("client_id") == client_id]
    indicators = calculate_client_indicators(client_id)
    return {**client, "stakeholders": stakeholders, "indicators": indicators}

@app.get("/clients/{client_id}/indicators")
def get_client_indicators(client_id: str, reference_date: Optional[str] = Query(default=None)):
    find_or_404(load_clients(), client_id, "Client")
    return calculate_client_indicators(client_id, reference_date=reference_date)

@app.get("/people")
def get_people():
    return load_people()

@app.post("/people")
def create_person(payload: PersonCreateRequest):
    people = load_people()
    person_id = payload.id or f"person_{uuid.uuid4().hex[:8]}"
    if any(person.get("id") == person_id for person in people):
        raise HTTPException(status_code=409, detail="Person id already exists")

    for client_id in payload.client_ids:
        find_or_404(load_clients(), client_id, "Client")

    timestamp = utc_now_iso()
    person = {
        "id": person_id,
        "name": payload.name,
        "email": payload.email,
        "aliases": payload.aliases,
        "notes": payload.notes,
        "labels": payload.labels,
        "client_ids": payload.client_ids,
        "is_temporary": payload.is_temporary,
        "voice_profile_id": payload.voice_profile_id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    people.append(person)
    save_people(people)
    log_audit_event("CREATE_PERSON", {"person_id": person_id, "name": payload.name, "temporary": payload.is_temporary})
    return {"success": True, "person": person}

@app.get("/people/{person_id}")
def get_person(person_id: str):
    person = find_or_404(load_people(), person_id, "Person")
    meetings = [meeting for meeting in load_meetings() if person_id in meeting.get("person_ids", [])]
    stakeholders = [item for item in load_stakeholders() if item.get("person_id") == person_id]
    action_items = [item for item in load_action_items() if item.get("assignee_person_id") == person_id]
    return {**person, "meetings": meetings, "stakeholders": stakeholders, "action_items": action_items}

@app.get("/stakeholders")
def get_stakeholders(client_id: Optional[str] = Query(default=None)):
    stakeholders = load_stakeholders()
    if client_id:
        stakeholders = [item for item in stakeholders if item.get("client_id") == client_id]
    return stakeholders

@app.post("/stakeholders")
def create_stakeholder(payload: StakeholderCreateRequest):
    clients = load_clients()
    people = load_people()
    find_or_404(clients, payload.client_id, "Client")
    find_or_404(people, payload.person_id, "Person")

    stakeholders = load_stakeholders()
    stakeholder_id = payload.id or f"stakeholder_{uuid.uuid4().hex[:8]}"
    if any(item.get("id") == stakeholder_id for item in stakeholders):
        raise HTTPException(status_code=409, detail="Stakeholder id already exists")

    timestamp = utc_now_iso()
    stakeholder = {
        "id": stakeholder_id,
        "client_id": payload.client_id,
        "person_id": payload.person_id,
        "role": payload.role,
        "influence_level": payload.influence_level,
        "notes": payload.notes,
        "labels": payload.labels,
        "is_primary": payload.is_primary,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    stakeholders.append(stakeholder)
    save_stakeholders(stakeholders)
    log_audit_event(
        "CREATE_STAKEHOLDER",
        {"stakeholder_id": stakeholder_id, "client_id": payload.client_id, "person_id": payload.person_id},
    )
    return {"success": True, "stakeholder": stakeholder}

@app.get("/action-items")
def get_action_items(client_id: Optional[str] = Query(default=None), status: Optional[str] = Query(default=None)):
    action_items = load_action_items()
    if client_id:
        action_items = [item for item in action_items if item.get("client_id") == client_id]
    if status:
        action_items = [item for item in action_items if item.get("status") == status]
    return action_items

@app.post("/action-items")
def create_action_item(payload: ActionItemCreateRequest):
    if payload.client_id:
        find_or_404(load_clients(), payload.client_id, "Client")
    if payload.assignee_person_id:
        find_or_404(load_people(), payload.assignee_person_id, "Person")
    if payload.suggested_assignee_person_id:
        find_or_404(load_people(), payload.suggested_assignee_person_id, "Person")
    if payload.meeting_id:
        find_or_404(load_meetings(), payload.meeting_id, "Meeting")

    action_items = load_action_items()
    action_item_id = payload.id or f"action_{uuid.uuid4().hex[:8]}"
    if any(item.get("id") == action_item_id for item in action_items):
        raise HTTPException(status_code=409, detail="Action item id already exists")

    timestamp = utc_now_iso()
    action_item = {
        "id": action_item_id,
        "title": payload.title,
        "client_id": payload.client_id,
        "meeting_id": payload.meeting_id,
        "assignee_person_id": payload.assignee_person_id,
        "suggested_assignee_person_id": payload.suggested_assignee_person_id,
        "status": payload.status,
        "priority": payload.priority,
        "due_date": payload.due_date,
        "labels": payload.labels,
        "notes": payload.notes,
        "evidence": [item.dict() for item in payload.evidence],
        "source": payload.source,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    action_items.append(action_item)
    save_action_items(action_items)
    log_audit_event(
        "CREATE_ACTION_ITEM",
        {"action_item_id": action_item_id, "client_id": payload.client_id, "meeting_id": payload.meeting_id},
    )
    return {"success": True, "action_item": action_item}

@app.websocket("/stream/transcription")
@app.websocket("/ws/transcription")
async def websocket_transcription(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_transcription(data: dict):
    await manager.send_transcription(data)

if __name__ == "__main__":
    import uvicorn
    settings = load_settings()
    threading.Thread(target=start_queue_workers_on_boot, args=(settings,), daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
