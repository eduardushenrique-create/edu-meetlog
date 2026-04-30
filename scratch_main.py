import sys
import os
import time
import requests
import subprocess
from pathlib import Path

# Provide a sample meeting audio
sample_audio = Path("c:/Users/eduar/OneDrive/Desktop/Edu MeetLog/backend/queue/pending/meeting_dummy_mixed_0.wav")

import shutil
from backend.paths import APP_DATA_DIR

app_queue_pending = APP_DATA_DIR / "queue" / "pending"
app_queue_pending.mkdir(parents=True, exist_ok=True)

dest_wav = app_queue_pending / "meeting_dummy_mixed_0.wav"
if sample_audio.exists():
    shutil.copy(sample_audio, dest_wav)
    print(f"Copied sample audio to {dest_wav}")

print("Starting backend...")
backend_proc = subprocess.Popen([sys.executable, "c:/PROJETOS/edu-meetlog/backend/main.py"])

time.sleep(5) # Wait for server to start

try:
    print("Checking queue stats...")
    res = requests.get("http://127.0.0.1:8000/status")
    print("Status:", res.json())

    print("Checking if test meeting processed...")
    while True:
        res = requests.get("http://127.0.0.1:8000/status")
        stats = res.json().get("queue_stats", {})
        print(f"Pending: {stats.get('pending')}, Processing: {stats.get('processing')}, Done: {stats.get('done')}, Failed: {stats.get('failed')}")
        if stats.get('pending') == 0 and stats.get('processing') == 0:
            print("Queue is empty.")
            break
        time.sleep(5)
finally:
    backend_proc.terminate()
    backend_proc.wait()
