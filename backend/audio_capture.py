import soundcard as sc
import soundfile as sf
import numpy as np
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock
from collections import deque
import time

SAMPLE_RATE = 16000
CHANNELS = 1
SEGMENT_DURATION = 300
CHUNK_DURATION = 3
RECORDINGS_DIR = Path(__file__).parent.parent / "recordings"

class ChunkBuffer:
    def __init__(self, max_duration=3):
        self.buffer = deque()
        self.max_samples = SAMPLE_RATE * max_duration
        self.lock = Lock()
        self.current_chunk = np.array([])
    
    def add(self, audio_data):
        with self.lock:
            self.current_chunk = np.concatenate([self.current_chunk, audio_data])
            while len(self.current_chunk) > self.max_samples:
                self.buffer.append(self.current_chunk[:self.max_samples])
                self.current_chunk = self.current_chunk[self.max_samples:]
    
    def get_chunks(self):
        with self.lock:
            chunks = list(self.buffer)
            self.buffer.clear()
            if len(self.current_chunk) >= SAMPLE_RATE:
                chunks.append(self.current_chunk)
                self.current_chunk = np.array([])
            return chunks
    
    def clear(self):
        with self.lock:
            self.buffer.clear()
            self.current_chunk = np.array([])

class AudioCapture:
    def __init__(self, mic_enabled=True, system_enabled=False):
        self.mic_enabled = mic_enabled
        self.system_enabled = system_enabled
        self.recording = False
        self.paused = False
        self.mic_buffer = []
        self.system_buffer = []
        self.mic_chunk_buffer = ChunkBuffer(CHUNK_DURATION)
        self.system_chunk_buffer = ChunkBuffer(CHUNK_DURATION)
        self.session_start = None
        self.segment_start = None
        self.pause_start = None
        self.total_paused_time = 0.0
        self._threads = []
        
    def list_devices(self):
        return {"mics": [m.name for m in sc.all_microphones()]}
    
    def start(self):
        if self.recording:
            return {"success": False, "message": "Already recording"}
            
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime.now()
        self.segment_start = datetime.now()
        self.pause_start = None
        self.total_paused_time = 0.0
        self.recording = True
        self.paused = False
        self.mic_buffer = []
        self.system_buffer = []
        self.mic_chunk_buffer.clear()
        self.system_chunk_buffer.clear()
        self._threads = []
        
        if self.mic_enabled:
            mic = sc.default_microphone()
            t = Thread(target=self._record_loop, args=(mic, self.mic_buffer, "mic"), daemon=True)
            t.start()
            self._threads.append(t)
            
        if self.system_enabled:
            try:
                spk = sc.default_speaker()
                print(f"[system] Speaker: {spk.name}")
                system_mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
                t = Thread(target=self._record_loop, args=(system_mic, self.system_buffer, "system"), daemon=True)
                t.start()
                self._threads.append(t)
            except Exception as e:
                print(f"[system] Erro ao obter dispositivo de loopback: {e}")
                print(f"[system] Tentando com default_microphone como fallback...")
                try:
                    system_mic = sc.default_microphone()
                    t = Thread(target=self._record_loop, args=(system_mic, self.system_buffer, "system"), daemon=True)
                    t.start()
                    self._threads.append(t)
                except Exception as e2:
                    print(f"[system] Fallback também falhou: {e2}")
            
        Thread(target=self._segment_writer, daemon=True).start()
        
        return {"success": True, "message": "Recording started"}
        
    def _record_loop(self, mic, buffer, name):
        try:
            with mic.recorder(samplerate=SAMPLE_RATE, channels=CHANNELS) as rec:
                print(f"[{name}] Capturando de: {mic.name}")
                while self.recording:
                    data = rec.record(numframes=SAMPLE_RATE // 2)
                    if self.recording and not self.paused:
                        # Marca o tempo em que o chunk terminou de ser gravado
                        current_time = time.time()
                        buffer.append((current_time, data))
                        
                        chunk_buffer = self.mic_chunk_buffer if name == "mic" else self.system_chunk_buffer
                        chunk_buffer.add(data.flatten())
        except Exception as e:
            print(f"Erro capturando áudio de {name} ({mic.name}): {e}")

    def _segment_writer(self):
        while self.recording:
            time.sleep(SEGMENT_DURATION)
            if self.recording and not self.paused:
                self._save_segment()
                self.segment_start = datetime.now()

    def _save_segment(self):
        timestamp = self.segment_start.strftime("%Y-%m-%d_%H%M%S")
        
        mic_data = self.mic_buffer[:]
        self.mic_buffer.clear()
        
        sys_data = self.system_buffer[:]
        self.system_buffer.clear()
        
        all_chunks = []
        if mic_data:
            all_chunks.extend(mic_data)
        if sys_data:
            all_chunks.extend(sys_data)
            
        if not all_chunks:
            return
            
        # Calcula o inicio e o fim global (tempo real) para manter o sincronismo
        first_time = min(t - len(d)/SAMPLE_RATE for t, d in all_chunks)
        last_time = max(t for t, d in all_chunks)
        
        total_duration = last_time - first_time
        total_samples = int(np.ceil(total_duration * SAMPLE_RATE))
        
        # Cria arrays baseados no tempo total e preenche os chunks nos locais exatos
        mic_audio = np.zeros((total_samples, CHANNELS), dtype=np.float32)
        sys_audio = np.zeros((total_samples, CHANNELS), dtype=np.float32)
        
        for t, d in mic_data:
            duration = len(d) / SAMPLE_RATE
            start_t = t - duration
            offset = int((start_t - first_time) * SAMPLE_RATE)
            end_offset = offset + len(d)
            if offset >= 0 and end_offset <= total_samples:
                mic_audio[offset:end_offset] += d
                
        for t, d in sys_data:
            duration = len(d) / SAMPLE_RATE
            start_t = t - duration
            offset = int((start_t - first_time) * SAMPLE_RATE)
            end_offset = offset + len(d)
            if offset >= 0 and end_offset <= total_samples:
                sys_audio[offset:end_offset] += d

        audio_to_save = None
        if mic_data and sys_data:
            filename = RECORDINGS_DIR / f"{timestamp}_mixed.wav"
            mixed_audio = np.zeros((total_samples, CHANNELS), dtype=np.float32)
            # Dá um leve ganho no microfone para evitar que seja ofuscado pelo sistema
            mixed_audio += mic_audio * 1.5
            mixed_audio += sys_audio
            
            with sf.SoundFile(str(filename), mode='w', samplerate=SAMPLE_RATE, channels=CHANNELS, subtype='PCM_16') as f:
                f.write(np.clip(mixed_audio, -1.0, 1.0))
            print(f"[capture] Salvo: {filename.name}")
            return
        elif mic_data:
            audio_to_save = mic_audio
        elif sys_data:
            audio_to_save = sys_audio
            
        if audio_to_save is not None:
            filename = RECORDINGS_DIR / f"{timestamp}_mixed.wav"
            with sf.SoundFile(str(filename), mode='w', samplerate=SAMPLE_RATE, channels=CHANNELS, subtype='PCM_16') as f:
                f.write(np.clip(audio_to_save, -1.0, 1.0))
            print(f"[capture] Salvo: {filename.name}")

    def stop(self):
        if not self.recording:
            return {"success": False, "message": "Not recording"}
            
        self.recording = False
        self.paused = False
        time.sleep(1.0)
        
        self._save_segment()
        
        duration = (datetime.now() - self.session_start).total_seconds() - self.total_paused_time
        
        return {"success": True, "message": "Recording stopped", "duration": duration}
    
    def pause(self):
        if not self.recording:
            return {"success": False, "message": "Not recording"}
        if self.paused:
            return {"success": False, "message": "Already paused"}
        
        self.paused = True
        self.pause_start = datetime.now()
        return {"success": True, "message": "Recording paused"}
    
    def resume(self):
        if not self.recording:
            return {"success": False, "message": "Not recording"}
        if not self.paused:
            return {"success": False, "message": "Not paused"}
        
        if self.pause_start:
            self.total_paused_time += (datetime.now() - self.pause_start).total_seconds()
        self.paused = False
        self.pause_start = None
        return {"success": True, "message": "Recording resumed"}
    
    def get_realtime_chunks(self):
        mic_chunks = self.mic_chunk_buffer.get_chunks()
        system_chunks = self.system_chunk_buffer.get_chunks()
        return {"mic": mic_chunks, "system": system_chunks}

if __name__ == "__main__":
    capture = AudioCapture(mic_enabled=True, system_enabled=True)
    capture.start()
    print("Gravando por 5s...")
    time.sleep(5)
    capture.stop()
    print("Finalizado!")
