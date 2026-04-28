import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import shutil
import time
import threading
import uuid
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from pathlib import Path

from audio_capture import AudioCapture, SAMPLE_RATE
from queue_worker import check_and_combine_transcripts, start_workers as start_queue_workers
from gpu_detection import detect_device
from meeting_detection import MeetingDetector, ProcessMonitor
from diarization import DiarizationEngine, align_speakers_to_transcript
from realtime_transcriber import RealtimeTranscriber
from transcription.merge_engine import TranscriptMergeEngine

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

RECORDINGS_DIR = Path(__file__).parent.parent / "recordings"
QUEUE_DIR = Path(__file__).parent / "queue"
CONFIG_DIR = Path(__file__).parent.parent / "config"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"
MEETINGS_FILE = CONFIG_DIR / "meetings.json"

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "pending").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "processing").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "done").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "failed").mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

app_state = {
    "state": "IDLE",
    "session_start": None,
    "recording_duration": 0,
    "current_meeting_id": None,
    "mic_enabled": True,
    "system_enabled": False,
}

meeting_detector = MeetingDetector()
process_monitor = ProcessMonitor()
process_monitor.start()

realtime_transcriber = None
realtime_merge_engine = TranscriptMergeEngine(overlap_policy="keep_both")
realtime_thread = None
realtime_running = False
realtime_meeting_id = None
realtime_offsets = {"mic": 0.0, "system": 0.0}
realtime_lock = threading.Lock()


def _broadcast_transcription_from_thread(payload: dict):
    manager.send_transcription_from_thread(payload)


def _process_realtime_source_chunks(meeting_id: str, source: str, chunks: list):
    global realtime_offsets
    global realtime_transcriber

    if realtime_transcriber is None:
        return

    speaker = "user" if source == "mic" else "system"

    for chunk in chunks:
        if chunk is None or len(chunk) == 0:
            continue

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

        _broadcast_transcription_from_thread(
            {
                "meeting_id": meeting_id,
                "is_partial": True,
                "segments": merge_result.new_segments,
                "final_transcript": {
                    "segments": merge_result.merged_segments,
                },
            }
        )


def _realtime_worker_loop(meeting_id: str):
    global realtime_running

    while realtime_running and app_state.get("current_meeting_id") == meeting_id:
        if app_state.get("state") == "PAUSED":
            time.sleep(0.2)
            continue

        chunks = capture.get_realtime_chunks()
        _process_realtime_source_chunks(meeting_id, "mic", chunks.get("mic", []))
        _process_realtime_source_chunks(meeting_id, "system", chunks.get("system", []))
        time.sleep(0.2)


def start_realtime_pipeline(meeting_id: str, model_name: str):
    global realtime_running
    global realtime_meeting_id
    global realtime_thread
    global realtime_offsets
    global realtime_transcriber

    stop_realtime_pipeline()

    with realtime_lock:
        realtime_running = True
        realtime_meeting_id = meeting_id
        realtime_offsets = {"mic": 0.0, "system": 0.0}

    realtime_merge_engine.clear_stream(meeting_id)

    if realtime_transcriber is None or realtime_transcriber.model_name != model_name:
        realtime_transcriber = RealtimeTranscriber(model_name=model_name)
    realtime_transcriber.start()

    realtime_thread = threading.Thread(target=_realtime_worker_loop, args=(meeting_id,), daemon=True)
    realtime_thread.start()


def stop_realtime_pipeline():
    global realtime_running
    global realtime_meeting_id
    global realtime_thread
    global realtime_transcriber

    with realtime_lock:
        meeting_id = realtime_meeting_id
        realtime_running = False
        realtime_meeting_id = None

    if realtime_thread and realtime_thread.is_alive():
        realtime_thread.join(timeout=1.0)
    realtime_thread = None

    if realtime_transcriber is not None:
        realtime_transcriber.stop()

    capture.mic_chunk_buffer.clear()
    capture.system_chunk_buffer.clear()

    if meeting_id:
        realtime_merge_engine.clear_stream(meeting_id)

def load_settings():
    settings_file = CONFIG_DIR / "settings.json"
    if settings_file.exists():
        return json.loads(settings_file.read_text())
    return {"mic_enabled": True, "system_enabled": False, "model": "large-v3", "workers": 2, "auto_start": False}

def save_settings(settings: dict):
    settings_file = CONFIG_DIR / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2))

def load_meetings():
    if MEETINGS_FILE.exists():
        return json.loads(MEETINGS_FILE.read_text())
    return []

def save_meetings(meetings: list):
    MEETINGS_FILE.write_text(json.dumps(meetings, indent=2))

def add_meeting(meeting: dict):
    meetings = load_meetings()
    existing = next((m for m in meetings if m["id"] == meeting["id"]), None)
    if existing:
        existing.update(meeting)
    else:
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
    pending_meetings = set()
    for f in (QUEUE_DIR / "pending").glob("*_mixed_*.wav"):
        parts = f.stem.rsplit("_", 2)
        pending_meetings.add(parts[0])
    
    processing_meetings = set()
    for f in (QUEUE_DIR / "processing").glob("*_mixed_*.wav"):
        parts = f.stem.rsplit("_", 2)
        processing_meetings.add(parts[0])
    
    done_meetings = set()
    for f in (QUEUE_DIR / "done").glob("meeting_*.json"):
        stem = f.stem
        if "_mic_" in stem or "_system_" in stem or "_mixed_" in stem:
            continue
        done_meetings.add(stem)
    
    failed_meetings = set()
    for f in (QUEUE_DIR / "failed").glob("meeting_*.wav"):
        stem = f.stem
        if "_mic_" in stem or "_system_" in stem or "_mixed_" in stem:
            failed_meetings.add(stem.rsplit("_", 2)[0])
        else:
            failed_meetings.add(stem)
    
    pending_count = len(pending_meetings - processing_meetings)
    processing_count = len(processing_meetings)
    
    return {
        "pending": pending_count,
        "processing": processing_count,
        "done": len(done_meetings),
        "failed": len(failed_meetings)
    }

def move_to_queue(audio_path: Path, meeting_id: str, audio_type: str = "mic", segment_index: int = 0):
    dest = QUEUE_DIR / "pending" / f"{meeting_id}_{audio_type}_{segment_index}.wav"
    meta_dest = QUEUE_DIR / "pending" / f"{meeting_id}_{audio_type}_{segment_index}.meta.json"
    try:
        if dest.exists():
            dest.unlink()
        shutil.copy(str(audio_path), str(dest))
        meta_dest.write_text(json.dumps({"audio_type": audio_type, "attempts": 0, "segment_index": segment_index}))
    except Exception as e:
        print(f"Error moving file: {e}")

def start_queue_workers_on_boot(settings: dict):
    workers_count = settings.get("workers", 2)
    model_name = settings.get("model", "large-v3")
    start_queue_workers(workers_count, model_name)

class RecordingRequest(BaseModel):
    mic_enabled: bool = True
    system_enabled: bool = False
    segment_duration: int = 300

class Settings(BaseModel):
    mic_enabled: bool = True
    system_enabled: bool = False
    model: str = "large-v3"
    workers: int = 2
    auto_start: bool = False

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
            session_files: list[Path] = []

            if session_start:
                session_files = [
                    f for f in RECORDINGS_DIR.glob("*.wav")
                    if f.stat().st_size > 0 and f.stat().st_mtime >= session_start
                ]
            else:
                session_start_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                session_files = [
                    f for f in RECORDINGS_DIR.glob("*.wav")
                    if f.stat().st_size > 0 and session_start_time in f.stem
                ]

            session_files = sorted(session_files, key=lambda f: f.stat().st_mtime)

            if session_files:
                segments_by_time = {}
                for wav_file in session_files:
                    parts = wav_file.stem.rsplit("_", 2)
                    if len(parts) != 3:
                        continue
                    time_key = "_".join(parts[:-1])
                    audio_type = parts[-1]
                    if audio_type != "mixed":
                        continue
                    if time_key not in segments_by_time:
                        segments_by_time[time_key] = []
                    segments_by_time[time_key].append((wav_file, audio_type))

                if segments_by_time:
                    date_str = datetime.now().strftime("%d %b, %H:%M")

                    add_meeting({
                        "id": meeting_id,
                        "name": f"Reuniao {date_str}",
                        "date": date_str,
                        "duration": format_duration(duration),
                        "status": "pending",
                        "segments": len(segments_by_time),
                        "wav_file": ", ".join([f.name for f in session_files]),
                    })

                    for idx, (_, files) in enumerate(sorted(segments_by_time.items())):
                        for wav_file, audio_type in files:
                            move_to_queue(wav_file, meeting_id, audio_type, idx)
                    update_meeting_status(meeting_id, "pending")

        app_state["current_meeting_id"] = None
        app_state["recording_duration"] = 0
        app_state["session_start"] = None

    return {
        "success": result["success"],
        "message": result["message"],
        "duration": duration,
        "meeting_id": meeting_id,
    }

@app.post("/recording/start")
def start_recording(req: RecordingRequest):
    global app_state

    if app_state["state"] == "RECORDING":
        raise HTTPException(status_code=400, detail="Already recording")

    capture.mic_enabled = req.mic_enabled
    capture.system_enabled = req.system_enabled

    result = capture.start()

    if result["success"]:
        app_state["state"] = "RECORDING"
        app_state["mic_enabled"] = req.mic_enabled
        app_state["system_enabled"] = req.system_enabled
        app_state["session_start"] = time.time()
        meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
        app_state["current_meeting_id"] = meeting_id
        app_state["recording_duration"] = 0

        if req.mic_enabled or req.system_enabled:
            settings = load_settings()
            start_realtime_pipeline(meeting_id=meeting_id, model_name=settings.get("model", "large-v3"))

    return {"success": result["success"], "message": result["message"], "meeting_id": app_state["current_meeting_id"]}

@app.post("/recording/pause")
def pause_recording():
    global app_state

    if app_state["state"] != "RECORDING":
        raise HTTPException(status_code=400, detail="Not recording")

    result = capture.pause()

    if result["success"]:
        app_state["state"] = "PAUSED"

    return result

@app.post("/recording/resume")
def resume_recording():
    global app_state

    if app_state["state"] != "PAUSED":
        raise HTTPException(status_code=400, detail="Not paused")

    result = capture.resume()

    if result["success"]:
        app_state["state"] = "RECORDING"

    return result

@app.post("/recording/finalize")
def finalize_recording():
    global app_state

    if app_state["state"] not in ["RECORDING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Not recording")

    return finalize_current_recording()

@app.post("/recording/stop")
def stop_recording():
    global app_state

    if app_state["state"] not in ["RECORDING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Not recording")

    return finalize_current_recording()

def format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

@app.get("/status")
def get_status():
    global app_state

    if app_state["state"] == "RECORDING" and app_state["session_start"]:
        app_state["recording_duration"] = time.time() - app_state["session_start"]

    device_info = detect_device()
    
    return {
        "state": app_state["state"],
        "recording_duration": app_state["recording_duration"],
        "mic_enabled": app_state["mic_enabled"],
        "system_enabled": app_state["system_enabled"],
        "queue_stats": get_queue_stats(),
        "settings": load_settings(),
        "meeting_id": app_state.get("current_meeting_id"),
        "gpu": {
            "available": device_info["cuda_available"],
            "device": device_info["device"],
            "compute_type": device_info["compute_type"],
            "gpu_info": device_info["gpu_info"]
        }
    }

@app.get("/meetings")
def get_meetings():
    meetings = load_meetings()
    for m in meetings:
        meeting_id = m['id']
        wav_exists = any((QUEUE_DIR / "pending").glob(f"{meeting_id}_*_*.wav"))
        wav_proc = any((QUEUE_DIR / "processing").glob(f"{meeting_id}_*_*.wav"))
        json_done = (QUEUE_DIR / "done" / f"{meeting_id}.json").exists()
        json_done_segments = any((QUEUE_DIR / "done").glob(f"{meeting_id}_*_*.json"))
        json_failed = any((QUEUE_DIR / "failed").glob(f"{meeting_id}_*_*.wav"))
        
        if wav_proc:
            m["status"] = "processing"
        elif wav_exists:
            m["status"] = "pending"
        elif json_done:
            m["status"] = "done"
        elif json_failed:
            m["status"] = "failed"
        else:
            m["status"] = "pending"
    return sorted(meetings, key=lambda m: m.get("date", ""), reverse=True)

@app.get("/transcripts/{meeting_id}")
def get_transcript(meeting_id: str):
    for search_dir in [QUEUE_DIR / "done", TRANSCRIPTS_DIR]:
        transcript_file = search_dir / f"{meeting_id}.json"
        if transcript_file.exists():
            transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
            if "meeting_id" not in transcript:
                transcript["meeting_id"] = meeting_id
            if "final_transcript" not in transcript:
                transcript["final_transcript"] = {"segments": transcript.get("segments", [])}
            if "segments" not in transcript:
                transcript["segments"] = transcript["final_transcript"].get("segments", [])
            return transcript
        for seg_file in search_dir.glob(f"{meeting_id}_*_*.json"):
            transcript = json.loads(seg_file.read_text(encoding="utf-8"))
            segments = transcript.get("segments", [])
            return {
                "meeting_id": meeting_id,
                "final_transcript": {"segments": segments},
                "segments": segments,
            }

    if check_and_combine_transcripts(meeting_id, finalize=False):
        transcript_file = QUEUE_DIR / "done" / f"{meeting_id}.json"
        if transcript_file.exists():
            transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
            if "meeting_id" not in transcript:
                transcript["meeting_id"] = meeting_id
            if "final_transcript" not in transcript:
                transcript["final_transcript"] = {"segments": transcript.get("segments", [])}
            if "segments" not in transcript:
                transcript["segments"] = transcript["final_transcript"].get("segments", [])
            return transcript

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
    return {
        "meeting_active": meeting_detector.is_meeting_active,
        "active_apps": list(process_monitor.get_active_meeting_apps()),
        "vad_enabled": meeting_detector.running
    }

@app.post("/transcripts/{meeting_id}/diarize")
def diarize_transcript(meeting_id: str):
    transcript_file = QUEUE_DIR / "done" / f"{meeting_id}.json"
    if not transcript_file.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
    
    aligned = align_speakers_to_transcript(
        transcript.get("segments", []),
        {},
        {}
    )
    
    transcript["segments"] = aligned
    transcript["final_transcript"] = {"segments": aligned}
    transcript_file.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return {"success": True, "segments": aligned}

@app.post("/popup/show")
def show_popup(popup_type: str, title: str, message: str, buttons: list = None):
    return {
        "success": True,
        "type": popup_type,
        "title": title,
        "message": message,
        "buttons": buttons or [],
        "id": f"popup_{int(time.time())}"
    }

@app.websocket("/ws/transcription")
async def websocket_transcription(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_transcription(data: dict):
    await manager.send_transcription(data)

if __name__ == "__main__":
    import uvicorn
    settings = load_settings()

    queue_thread = threading.Thread(
        target=start_queue_workers_on_boot,
        args=(settings,),
        daemon=True
    )
    queue_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=8000)
