import numpy as np
from collections import deque

class VAD:
    def __init__(self, sample_rate=16000, frame_duration=20, aggressiveness=2):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration / 1000)
        self.aggressiveness = aggressiveness
        self.threshold = self._get_threshold()
        
    def _get_threshold(self):
        thresholds = {0: 0.5, 1: 0.4, 2: 0.3, 3: 0.25}
        return thresholds.get(self.aggressiveness, 0.35)
    
    def is_speech(self, audio_frame):
        if len(audio_frame) < self.frame_size:
            audio_frame = np.pad(audio_frame, (0, self.frame_size - len(audio_frame)))
        
        rms = np.sqrt(np.mean(audio_frame ** 2))
        return rms > self.threshold
    
    def is_speech_energy(self, audio_frame):
        if len(audio_frame) < self.frame_size:
            return False
        energy = np.abs(audio_frame).mean()
        return energy > self.threshold

class SpeechDetector:
    def __init__(self, sample_rate=16000, min_speech_duration=0.3, silence_duration=2.0):
        self.sample_rate = sample_rate
        self.min_speech_duration = min_speech_duration
        self.silence_duration = silence_duration
        self.vad = VAD(sample_rate)
        self.speech_buffer = deque()
        self.silence_counter = 0
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        
    def process_frame(self, audio_frame):
        has_speech = self.vad.is_speech_energy(audio_frame)
        current_time = 0
        
        if has_speech:
            if not self.is_speaking:
                self.is_speaking = True
                self.speech_start_time = current_time
            self.speech_buffer.append(audio_frame)
            self.silence_counter = 0
        else:
            if self.is_speaking:
                self.silence_counter += 1
                if self.silence_counter > (self.silence_duration * 1000 / 20):
                    self.is_speaking = False
                    speech_data = np.concatenate(list(self.speech_buffer))
                    self.speech_buffer.clear()
                    return {"type": "speech_end", "audio": speech_data}
        return {"type": "frame", "has_speech": has_speech}
    
    def reset(self):
        self.speech_buffer.clear()
        self.silence_counter = 0
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None

if __name__ == "__main__":
    vad = VAD()
    print(f"VAD initialized with threshold: {vad.threshold}")
    
    detector = SpeechDetector()
    print(f"SpeechDetector ready")