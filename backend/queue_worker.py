import os
import shutil
import time
import json
from pathlib import Path
from threading import Thread
from faster_whisper import WhisperModel

QUEUE_DIR = Path("queue")
PENDING = QUEUE_DIR / "pending"
PROCESSING = QUEUE_DIR / "processing"
DONE = QUEUE_DIR / "done"
FAILED = QUEUE_DIR / "failed"
RECORDINGS_DIR = Path("recordings")

PENDING.mkdir(parents=True, exist_ok=True)
PROCESSING.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)
FAILED.mkdir(parents=True, exist_ok=True)

MAX_ATTEMPTS = 3

model_cache = {}

def get_model(model_name: str = "large-v3"):
    if model_name not in model_cache:
        print(f"Loading model {model_name}...")
        model_cache[model_name] = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8"
        )
        print(f"Model {model_name} loaded!")
    return model_cache[model_name]

def transcribe_audio(audio_path: Path, model_name: str = "large-v3"):
    model = get_model(model_name)
    
    segments, info = model.transcribe(
        str(audio_path),
        language="pt",
        beam_size=5,
        vad_filter=True
    )
    
    result_segments = []
    for i, segment in enumerate(segments):
        text = segment.text.strip()
        if text:
            start = segment.start
            end = segment.end
            
            speaker = "user" if "user" in text.lower() or start < 5 else "other"
            
            result_segments.append({
                "id": i,
                "start": round(start, 2),
                "end": round(end, 2),
                "speaker": speaker,
                "text": text
            })
    
    return {"segments": result_segments}

def process_file(audio_file: Path, model_name: str = "large-v3"):
    meta_file = audio_file.with_suffix('.meta.json')
    
    attempts = 0
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
        attempts = meta.get("attempts", 0)
    
    try:
        result = transcribe_audio(audio_file, model_name)
        
        output_file = DONE / f"{audio_file.stem}.json"
        output_file.write_text(json.dumps(result, indent=2))
        
        audio_file.unlink()
        if meta_file.exists():
            meta_file.unlink()
        
        return True
    except Exception as e:
        print(f"Error processing {audio_file}: {e}")
        attempts += 1
        
        meta = {"attempts": attempts, "max_attempts": MAX_ATTEMPTS}
        meta_file.write_text(json.dumps(meta))
        
        if attempts >= MAX_ATTEMPTS:
            audio_file.rename(FAILED / audio_file.name)
            meta_file.rename(FAILED / meta_file.name)
        else:
            audio_file.rename(PENDING / audio_file.name)
        
        return False

def worker(worker_id: int, model_name: str = "large-v3", workers_count: int = 2):
    print(f"Worker {worker_id} started")
    
    while True:
        files = list(PENDING.glob("*.wav"))
        
        for audio_file in files:
            meta_file = audio_file.with_suffix('.meta.json')
            
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
                if meta.get("attempts", 0) > (worker_id % MAX_ATTEMPTS):
                    continue
            
            try:
                audio_file.rename(PROCESSING / audio_file.name)
            except:
                continue
            
            print(f"Worker {worker_id} processing {audio_file.name}")
            process_file(PROCESSING / audio_file.name, model_name)
        
        time.sleep(5)

def start_workers(workers_count: int = 2, model_name: str = "large-v3"):
    for i in range(workers_count):
        t = Thread(target=worker, args=(i, model_name, workers_count), daemon=True)
        t.start()
        print(f"Worker {i} started")

def get_queue_stats():
    return {
        "pending": len(list(PENDING.glob("*.wav"))),
        "processing": len(list(PROCESSING.glob("*.wav"))),
        "done": len(list(DONE.glob("*.json"))),
        "failed": len(list(FAILED.glob("*.json")))
    }

if __name__ == "__main__":
    print("Queue worker starting...")
    start_workers(workers_count=2, model_name="large-v3")
    
    while True:
        time.sleep(60)
        print(f"Queue stats: {get_queue_stats()}")