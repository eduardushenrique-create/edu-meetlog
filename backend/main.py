from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import threading
import time
from pathlib import Path
import json

from audio_capture import AudioCapture

app = FastAPI()
capture = AudioCapture()

RECORDINGS_DIR = Path("recordings")
QUEUE_DIR = Path("queue")
CONFIG_DIR = Path("config")

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "pending").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "processing").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "done").mkdir(parents=True, exist_ok=True)
(QUEUE_DIR / "failed").mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

app_state = {
    "state": "IDLE",
    "recording_duration": 0,
    "mic_enabled": True,
    "system_enabled": False,
    "session_start": None,
}


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


def load_settings():
    settings_file = CONFIG_DIR / "settings.json"
    if settings_file.exists():
        return json.loads(settings_file.read_text())
    return {"mic_enabled": True, "system_enabled": False, "model": "large-v3", "workers": 2, "auto_start": False}


def save_settings(settings: dict):
    settings_file = CONFIG_DIR / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2))


def get_queue_stats():
    pending = len(list((QUEUE_DIR / "pending").glob("*.wav")))
    processing = len(list((QUEUE_DIR / "processing").glob("*.wav")))
    done = len(list((QUEUE_DIR / "done").glob("*.json")))
    failed = len(list((QUEUE_DIR / "failed").glob("*.json")))
    return {"pending": pending, "processing": processing, "done": done, "failed": failed}


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
    
    return result


@app.post("/recording/stop")
def stop_recording():
    global app_state
    
    if app_state["state"] != "RECORDING":
        raise HTTPException(status_code=400, detail="Not recording")
    
    result = capture.stop()
    
    if result["success"]:
        app_state["state"] = "IDLE"
        app_state["recording_duration"] = result.get("duration", 0)
    
    return result


@app.get("/status")
def get_status():
    global app_state
    
    if app_state["state"] == "RECORDING" and app_state["session_start"]:
        app_state["recording_duration"] = time.time() - app_state["session_start"]
    
    return {
        "state": app_state["state"],
        "recording_duration": app_state["recording_duration"],
        "mic_enabled": app_state["mic_enabled"],
        "system_enabled": app_state["system_enabled"],
        "queue_stats": get_queue_stats(),
        "settings": load_settings(),
    }


@app.get("/meetings")
def get_meetings():
    meetings = []
    if RECORDINGS_DIR.exists():
        for folder in sorted(RECORDINGS_DIR.iterdir(), reverse=True):
            if folder.is_dir():
                meetings.append({
                    "id": folder.name,
                    "date": folder.name,
                    "duration": 0,
                    "status": "pending"
                })
    return meetings


@app.get("/transcripts/{meeting_id}")
def get_transcript(meeting_id: str):
    transcript_file = RECORDINGS_DIR / meeting_id / "transcript.json"
    if transcript_file.exists():
        return json.loads(transcript_file.read_text())
    raise HTTPException(status_code=404, detail="Transcript not found")


@app.post("/settings")
def update_settings(settings: Settings):
    save_settings(settings.dict())
    return {"success": True, "message": "Settings saved"}


@app.get("/settings")
def get_settings():
    return load_settings()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)