import subprocess
import os

def check_cuda_available():
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split(",")
            return {
                "name": lines[0].strip(),
                "memory": lines[1].strip(),
                "driver": lines[2].strip()
            }
    except Exception as e:
        print(f"Error getting GPU info: {e}")
    return None

def detect_device():
    """Detect the best available device for inference"""
    cuda_available = check_cuda_available()
    
    return {
        "cuda_available": cuda_available,
        "device": "cuda" if cuda_available else "cpu",
        "compute_type": "float16" if cuda_available else "int8",
        "gpu_info": get_gpu_info() if cuda_available else None
    }

if __name__ == "__main__":
    info = detect_device()
    print(f"Device: {info['device']}")
    print(f"CUDA available: {info['cuda_available']}")
    print(f"Compute type: {info['compute_type']}")
    if info['gpu_info']:
        print(f"GPU: {info['gpu_info']['name']}")