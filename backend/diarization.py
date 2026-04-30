import numpy as np
import os
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
    def __init__(self, use_pyannote=True):
        self.diarizer = SpeakerDiarizer()
        self.audio_sources = {}
        self.pipeline = None
        if use_pyannote:
            self.pipeline = self._load_pyannote_pipeline()

    def _load_pyannote_pipeline(self):
        try:
            from pyannote.audio import Pipeline
        except Exception:
            return None

        token = os.getenv("PYANNOTE_AUTH_TOKEN") or os.getenv("HF_TOKEN")
        try:
            return Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        except Exception as exc:
            print(f"Pyannote diarization unavailable: {exc}")
            return None

    def _process_with_pyannote(self, wav_path):
        diarization = self.pipeline(str(wav_path))
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": str(speaker),
            })
        return {"source": "pyannote", "segments": segments}
        
    def process_wav(self, wav_path):
        if self.pipeline is not None:
            try:
                return self._process_with_pyannote(wav_path)
            except Exception as e:
                print(f"Pyannote diarization error: {e}")

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
        if isinstance(audio_sources, dict) and isinstance(audio_sources.get("segments"), list):
            return align_transcript_with_diarization(
                transcript.get("segments", []),
                audio_sources["segments"],
            )
        return self.diarizer.align_transcript_to_speaker(
            transcript.get("segments", []),
            audio_sources
        )


def _overlap_seconds(a_start, a_end, b_start, b_end):
    return max(0.0, min(float(a_end), float(b_end)) - max(float(a_start), float(b_start)))


def align_transcript_with_diarization(transcript_segments, diarization_segments):
    aligned = []

    for seg in transcript_segments:
        seg_start = float(seg.get("start", 0))
        seg_end = float(seg.get("end", seg_start))
        best_speaker = None
        best_overlap = 0.0

        for diarized in diarization_segments:
            overlap = _overlap_seconds(
                seg_start,
                seg_end,
                diarized.get("start", 0),
                diarized.get("end", 0),
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diarized.get("speaker")

        next_seg = dict(seg)
        if best_speaker:
            next_seg["speaker"] = best_speaker
        aligned.append(next_seg)

    return aligned

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
