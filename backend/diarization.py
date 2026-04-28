import numpy as np
from collections import defaultdict
from vad import VAD

class SpeakerDiarizer:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.speakers = {}
        self.vad = VAD(sample_rate)
        self.energy_history = defaultdict(list)
        
    def process_audio(self, audio_data, source="mic"):
        if audio_data is None or len(audio_data) < self.sample_rate:
            return None
            
        rms = np.sqrt(np.mean(audio_data ** 2))
        is_speech = self.vad.is_speech_energy(audio_data)
        
        self.energy_history[source].append(rms)
        if len(self.energy_history[source]) > 10:
            self.energy_history[source].pop(0)
        
        return {
            "source": source,
            "energy": rms,
            "is_speech": is_speech
        }
    
    def get_active_speaker(self, threshold=0.05):
        avg_energies = {}
        for source, energies in self.energy_history.items():
            if energies:
                avg_energies[source] = np.mean(energies)
        
        if not avg_energies:
            return None
        
        max_source = max(avg_energies, key=avg_energies.get)
        return max_source if avg_energies[max_source] > threshold else None
    
    def align_transcript_to_speaker(self, transcript_segments, audio_sources):
        aligned = []
        
        for seg in transcript_segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_duration = seg_end - seg_start
            
            best_speaker = None
            best_overlap = 0
            
            for source in audio_sources:
                energy = audio_sources[source].get("energy", 0)
                if energy > best_overlap:
                    best_overlap = energy
                    best_speaker = source
            
            seg["speaker"] = best_speaker or seg.get("speaker", "unknown")
            aligned.append(seg)
        
        return aligned

class DiarizationEngine:
    def __init__(self):
        self.diarizer = SpeakerDiarizer()
        self.audio_sources = {}
        
    def process_wav(self, wav_path):
        try:
            import soundfile as sf
            audio, sr = sf.read(wav_path)
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            return self.diarizer.process_audio(audio, "audio")
        except Exception as e:
            print(f"Diarization error: {e}")
            return None
    
    def align_transcript(self, transcript, audio_sources):
        return self.diarizer.align_transcript_to_speaker(
            transcript.get("segments", []),
            audio_sources
        )

def align_speakers_to_transcript(transcript_segments, mic_energies, system_energies):
    aligned = []
    
    for seg in transcript_segments:
        seg_text = seg.get("text", "").lower()
        
        if "legenda" in seg_text or "subtitle" in seg_text:
            seg["speaker"] = "system"
        elif "mic" in seg_text or "user" in seg_text:
            seg["speaker"] = "user"
        else:
            seg["speaker"] = seg.get("speaker", "user")
        
        aligned.append(seg)
    
    return aligned

if __name__ == "__main__":
    engine = DiarizationEngine()
    print("DiarizationEngine ready")