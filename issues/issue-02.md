## Descrição
Implementar captura de áudio paralela usando microfone e sistema (loopback).

## Objetivos
- [ ] Configurar captura de áudio do microfone
- [ ] Configurar captura de áudio do sistema (loopback)
- [ ] Implementar captura paralela simultânea
- [ ] Sincronizar ambas as fontes por timestamp

## Tecnologias
- **Audio Capture**: Web Audio API + Tauri audio plugins
- **Backend**: Python (PyAudio, sounddevice) ou Rust (cpal)
- **Loopback**: VAC (Virtual Audio Cable) ou WASAPI

## Estratégia de captura
1. Usar Python com sounddevice para captura de áudio
2. Configurar 2 streams de áudio simultâneas:
   - Stream 1: Microfone (input)
   - Stream 2: Sistema/loopback (input)
3. Sincronizar timestamps de ambas as fontes

## Código base (Python)
```python
import sounddevice as sd
import numpy as np

# Configuração
SAMPLE_RATE = 16000
CHANNELS = 1

# Streams паралеlas
mic_stream = sd.InputStream(
    channels=CHANNELS,
    samplerate=SAMPLE_RATE,
    device=mic_device_index
)

system_stream = sd.InputStream(
    channels=CHANNELS,
    samplerate=SAMPLE_RATE,
    device=system_loopback_device_index
)
```

## Dispositivos necessários
- Microfone (dispositivo de entrada)
- Loopback virtual (ex: Virtual Audio Cable) para captura do sistema

## Referências
- https://python-sounddevice.readthedocs.io/
- https://github.com/ghn2faster-whisper