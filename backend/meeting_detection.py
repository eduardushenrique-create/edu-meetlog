import time
import threading
from collections import deque
from vad import SpeechDetector, VAD

MEETING_PROCESSES = ["zoom.exe", "teams.exe", "chrome.exe", "msedge.exe", "slack.exe"]

class MeetingDetector:
    def __init__(self, on_start=None, on_end=None):
        self.on_start = on_start
        self.on_end = on_end
        self.vad = SpeechDetector(min_speech_duration=0.5, silence_duration=3.0)
        self.running = False
        self.is_meeting_active = False
        self.meeting_start_time = None
        self.audio_callback = None
        self._thread = None
        
    def set_audio_callback(self, callback):
        self.audio_callback = callback
        
    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            
    def process_audio(self, audio_data):
        if not self.running:
            return None
        result = self.vad.process_frame(audio_data)
        return result
    
    def _detection_loop(self):
        print("Meeting detection loop started")
        
    def check_processes(self):
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in MEETING_PROCESSES:
                        return True
                except:
                    pass
        except:
            pass
        return False

class ProcessMonitor:
    def __init__(self):
        self.running = False
        self.active_processes = set()
        
    def start(self):
        self.running = True
        
    def stop(self):
        self.running = False
        
    def get_active_meeting_apps(self):
        try:
            import psutil
            active = set()
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name'].lower()
                    if name in MEETING_PROCESSES:
                        active.add(name)
                except:
                    pass
            return active
        except:
            return set()

if __name__ == "__main__":
    detector = MeetingDetector()
    print("MeetingDetector ready")
    
    monitor = ProcessMonitor()
    monitor.start()
    apps = monitor.get_active_meeting_apps()
    print(f"Active meeting apps: {apps}")