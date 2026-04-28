import soundfile as sf
import numpy as np
import os
import json

audio = np.zeros((16000,), dtype=np.float32)
sf.write('backend/queue/pending/meeting_dummy_mixed_0.wav', audio, 16000)

with open('backend/queue/pending/meeting_dummy_mixed_0.meta.json', 'w') as f:
    json.dump({"audio_type": "mixed", "segment_index": 0, "attempts": 0}, f)

print("Dummy gerado com sucesso!")
