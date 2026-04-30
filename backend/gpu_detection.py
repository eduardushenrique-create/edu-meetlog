import subprocess
import os


def check_cuda_available():
    """Check if nvidia-smi is present (driver installed)."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _ensure_nvidia_dlls_on_path():
    """Add pip-installed NVIDIA DLL directories to PATH and os.add_dll_directory.

    Packages like nvidia-cublas-cu12 install DLLs under
    site-packages/nvidia/<lib>/bin/ which is NOT on the system PATH.
    We scan for those directories and add them so ctypes.WinDLL can
    find cublas64_12.dll, cublasLt64_12.dll, etc.
    """
    import sys
    import site
    from pathlib import Path as _Path

    if sys.platform != "win32":
        return

    added = []
    for sp in site.getsitepackages() + [site.getusersitepackages()]:
        nvidia_dir = _Path(sp) / "nvidia"
        if not nvidia_dir.is_dir():
            continue
        for sub in nvidia_dir.iterdir():
            bin_dir = sub / "bin"
            if bin_dir.is_dir() and str(bin_dir) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
                # os.add_dll_directory is required on Python 3.8+ / Windows
                try:
                    os.add_dll_directory(str(bin_dir))
                except (OSError, AttributeError):
                    pass
                added.append(str(bin_dir))

    if added:
        print(f"[gpu] Added {len(added)} NVIDIA DLL dir(s) to PATH.")


def _cuda_runtime_works() -> bool:
    """Validate that CUDA runtime + cuBLAS actually work.

    nvidia-smi only checks the *driver*.  The cuBLAS/cuDNN DLLs that
    CTranslate2 needs might still be missing.  We do a cheap import-time
    probe so we never attempt GPU inference that will crash later.

    Note: ctranslate2.get_cuda_device_count() can return 1 even when
    cublas64_12.dll is missing, so we must probe the DLL directly.
    """
    import ctypes
    import sys

    if sys.platform == "win32":
        # Ensure pip-installed NVIDIA DLLs are discoverable
        _ensure_nvidia_dlls_on_path()

        # On Windows, CTranslate2 + faster-whisper need cublas64_12.dll
        for dll_name in ("cublas64_12.dll", "cublasLt64_12.dll"):
            try:
                ctypes.WinDLL(dll_name)
            except OSError:
                print(f"[gpu] {dll_name} not found — CUDA inference will fail.")
                return False
        return True
    else:
        # On Linux, check via ctranslate2
        try:
            import ctranslate2
            count = getattr(ctranslate2, "get_cuda_device_count", lambda: 0)()
            if count == 0:
                print("[gpu] ctranslate2 reports 0 CUDA devices.")
                return False
            return True
        except Exception as exc:
            print(f"[gpu] CUDA runtime probe failed: {exc}")
            return False


def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split(",")
            return {
                "name": lines[0].strip(),
                "memory": lines[1].strip(),
                "driver": lines[2].strip(),
            }
    except Exception as e:
        print(f"Error getting GPU info: {e}")
    return None


def detect_device():
    """Detect the best available device for inference.

    We check *both* the driver (nvidia-smi) and the CUDA runtime libs
    (cuBLAS DLLs) because faster-whisper / CTranslate2 needs both.
    """
    driver_ok = check_cuda_available()
    runtime_ok = _cuda_runtime_works() if driver_ok else False
    cuda_available = driver_ok and runtime_ok

    if driver_ok and not runtime_ok:
        print("[gpu] NVIDIA driver present but CUDA runtime libs missing — using CPU.")
        print("[gpu] To enable GPU: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12")

    return {
        "cuda_available": cuda_available,
        "device": "cuda" if cuda_available else "cpu",
        "compute_type": "float16" if cuda_available else "int8",
        "gpu_info": get_gpu_info() if driver_ok else None,
    }


if __name__ == "__main__":
    info = detect_device()
    print(f"Device: {info['device']}")
    print(f"CUDA available: {info['cuda_available']}")
    print(f"Compute type: {info['compute_type']}")
    if info['gpu_info']:
        print(f"GPU: {info['gpu_info']['name']}")