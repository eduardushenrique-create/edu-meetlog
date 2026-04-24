import sounddevice as sd
import numpy as np
import wave
import json
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

SAMPLE_RATE = 16000
CHANNELS = 1
SEGMENT_DURATION = 300
RECORDINGS_DIR = Path("recordings")


class AudioCapture:
    def __init__(self, mic_enabled=True, system_enabled=False):
        self.mic_enabled = mic_enabled
        self.system_enabled = system_enabled
        self.recording = False
        self.mic_stream = None
        self.system_stream = None
        self.mic_buffer = []
        self.system_buffer = []
        self.session_start = None
        self.segment_start = None
        
    def list_devices(self):
        devices = sd.query_devices()
        return devices
    
    def get_input_devices(self):
        return sd.query_devices(kind='input')
    
    def start(self):
        if self.recording:
            return {"success": False, "message": "Already recording"}
        
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime.now()
        self.segment_start = datetime.now()
        self.recording = True
        self.mic_buffer = []
        self.system_buffer = []
        
        if self.mic_enabled:
            self.mic_stream = sd.InputStream(
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                device=None,
                callback=self._mic_callback
            )
            self.mic_stream.start()
        
        if self.system_enabled:
            self.system_stream = sd.InputStream(
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                device=None,
                callback=self._system_callback
            )
            self.system_stream.start()
        
        Thread(target=self._segment_writer, daemon=True).start()
        
        return {"success": True, "message": "Recording started"}
    
    def _mic_callback(self, indata, frames, time, status):
        if status:
            print(f"Mic status: {status}")
        if self.recording:
            self.mic_buffer.append(indata.copy())
    
    def _system_callback(self, indata, frames, time, status):
        if status:
            print(f"System status: {status}")
        if self.recording:
            self.system_buffer.append(indata.copy())
    
    def _segment_writer(self):
        while self.recording:
            sd.sleep(SEGMENT_DURATION * 1000)
            if self.recording:
                self._save_segment()
                self.segment_start = datetime.now()
    
    def _save_segment(self):
        timestamp = self.segment_start.strftime("%Y-%m-%d_%H%M%S")
        
        if self.mic_buffer:
            audio_data = np.concatenate(self.mic_buffer)
            filename = RECORDINGS_DIR / f"{timestamp}_mic.wav"
            self._write_wav(filename, audio_data)
            self.mic_buffer = []
        
        if self.system_buffer:
            audio_data = np.concatenate(self.system_buffer)
            filename = RECORDINGS_DIR / f"{timestamp}_sys.wav"
            self._write_wav(filename, audio_data)
            self.system_buffer = []
    
    def _write_wav(self, filepath, audio_data):
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
    
    def stop(self):
        if not self.recording:
            return {"success": False, "message": "Not recording"}
        
        self.recording = False
        
        if self.mic_stream:
            self.mic_stream.stop()
            self.mic_stream = None
        
        if self.system_stream:
            self.system_stream.stop()
            self.system_stream = None
        
        if self.mic_buffer or self.system_buffer:
            self._save_segment()
        
        duration = (datetime.now() - self.session_start).total_seconds()
        
        return {"success": True, "message": "Recording stopped", "duration": duration}


if __name__ == "__main__":
    capture = AudioCapture(mic_enabled=True, system_enabled=False)
    print("Dispositivos de áudio:")
    print(sd.query_devices())