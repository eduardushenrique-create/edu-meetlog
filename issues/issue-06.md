## Descrição
Integrar faster-whisper para transcrição offline usando o modelo large-v3.

## Objetivos
- [ ] Instalar faster-whisper
- [ ] Baixar modelo large-v3
- [ ] Implementar transcrição de áudio
- [ ] Gerar formato com timestamps e speakers

## Instalação
```bash
pip install faster-whisper
```

## Modelo
- **Modelo**: large-v3
- **Tamanho**: ~3GB download inicial
- **Idioma**: Portuguese + multilingual

## Código de transcrição
```python
from faster_whisper import WhisperModel

# Carregar modelo (executar uma vez)
model = WhisperModel("large-v3", device="cuda", compute_type="int8")

# Transcrever
segments, info = model.transcribe(
    "audio.wav",
    language="pt",
    beam_size=5,
    vad_filter=True
)

for segment in segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
```

## Saída formatada
```json
{
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.2,
      "speaker": "user",
      "text": "Olá, bom dia!"
    },
    {
      "id": 1,
      "start": 3.5,
      "end": 6.8,
      "speaker": "other",
      "text": "Bom dia! Tudo bem?"
    }
  ]
}
```

## Formato de arquivo de transcrição
```
transcripts/
├── 2024-01-15_143000.json
└── 2024-01-15_143500.json
```

## Otimizações
- Usar GPU (CUDA) se disponível
- Usar compute_type=int8 para CPU
- VAD filter pararemover silêncios

## Detecção de speaker
- Usar transcription segmentada
- Assignar "user" para segmentos com maior energia
- Assignar "other" para demais

## Referências
- https://github.com/SYSTRAN/faster-whisper