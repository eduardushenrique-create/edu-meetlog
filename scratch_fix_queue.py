import re

def fix_queue_worker():
    with open('c:/Users/eduar/OneDrive/Desktop/Edu MeetLog/backend/queue_worker.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix get_model to be thread-safe
    target_get_model = """def get_model(model_name: str = "large-v3"):
    if model_name not in model_cache:
        device_info = detect_device()
        device = device_info["device"]
        compute_type = device_info["compute_type"]

        print(f"Loading model {model_name} on {device} ({compute_type})...")
        model_cache[model_name] = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
        print(f"Model {model_name} loaded on {device}!")
    return model_cache[model_name]"""

    replacement_get_model = """import threading
_model_lock = threading.Lock()

def get_model(model_name: str = "large-v3"):
    with _model_lock:
        if model_name not in model_cache:
            device_info = detect_device()
            device = device_info["device"]
            compute_type = device_info["compute_type"]

            print(f"Loading model {model_name} on {device} ({compute_type})...")
            model_cache[model_name] = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
            )
            print(f"Model {model_name} loaded on {device}!")
        return model_cache[model_name]"""
    
    content = content.replace(target_get_model, replacement_get_model)
    content = content.replace(target_get_model.replace('\n', '\r\n'), replacement_get_model)

    # 2. Fix the file pickup in worker loop
    target_worker_loop = """            try:
                if not dest_audio.exists():
                    audio_file.rename(dest_audio)
                if meta_file.exists() and not dest_meta.exists():
                    meta_file.rename(dest_meta)
            except Exception:
                continue

            print(f"Worker {worker_id} processing {audio_file.name}")
            success = process_file(PROCESSING / audio_file.name, model_name)"""

    replacement_worker_loop = """            try:
                audio_file.rename(dest_audio)
                if meta_file.exists():
                    meta_file.rename(dest_meta)
            except Exception:
                # File was already taken by another worker
                continue

            print(f"Worker {worker_id} processing {audio_file.name}")
            success = process_file(dest_audio, model_name)"""
            
    content = content.replace(target_worker_loop, replacement_worker_loop)
    content = content.replace(target_worker_loop.replace('\n', '\r\n'), replacement_worker_loop)

    # 3. Fix startup recovery
    target_startup = """def start_workers(workers_count: int = 2, model_name: str = "large-v3"):
    print("Executing startup recovery: moving stale processing files back to pending.")
    for stale_file in PROCESSING.glob("*.wav"):
        try:
            stale_file.replace(PENDING / stale_file.name)
        except Exception as exc:
            print(f"Failed to recover {stale_file.name}: {exc}")

    for i in range(workers_count):"""

    replacement_startup = """def start_workers(workers_count: int = 2, model_name: str = "large-v3"):
    print("Executing startup recovery: moving stale processing files back to pending.")
    for stale_file in PROCESSING.glob("*.wav"):
        try:
            stale_file.replace(PENDING / stale_file.name)
            stale_meta = PROCESSING / f"{stale_file.stem}.meta.json"
            if stale_meta.exists():
                stale_meta.replace(PENDING / stale_meta.name)
        except Exception as exc:
            print(f"Failed to recover {stale_file.name}: {exc}")

    for i in range(workers_count):"""

    content = content.replace(target_startup, replacement_startup)
    content = content.replace(target_startup.replace('\n', '\r\n'), replacement_startup)

    with open('c:/Users/eduar/OneDrive/Desktop/Edu MeetLog/backend/queue_worker.py', 'w', encoding='utf-8') as f:
        f.write(content)

fix_queue_worker()
print("Fixed queue_worker.py")
