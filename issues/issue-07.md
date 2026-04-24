## Descrição
Implementar sistema de armazenamento local com estrutura de diretórios.

## Estrutura de diretórios
```
.
├── recordings/      # Áudio gravado (.wav ou .flac)
├── transcripts/    # Transcrições (.json)
├── queue/          # Fila de processamento
│   ├── pending/
│   ├── processing/
│   ├── done/
│   └── failed/
└── config/         # Configurações do app
    └── settings.json
```

## recordings/
- Arquivos de áudio segmentados
- Formato: `{timestamp}_{source}.wav`
- Fonte: mic ou sys

## transcripts/
- Transcrições em JSON
- Formato: `{timestamp}.json`
- Conteúdo: segments com speaker e text

## config/settings.json
```json
{
  "mic_enabled": true,
  "system_enabled": true,
  "model": "large-v3",
  "workers": 2,
  "auto_start": false,
  "segment_duration": 300,
  "sample_rate": 16000
}
```

## Implementação
```python
from pathlib import Path
import json

BASE_DIR = Path(".")
RECORDINGS = BASE_DIR / "recordings"
TRANSCRIPTS = BASE_DIR / "transcripts"
QUEUE = BASE_DIR / "queue"
CONFIG = BASE_DIR / "config"

def init_dirs():
    for d in [RECORDINGS, TRANSCRIPTS, QUEUE]:
        d.mkdir(parents=True, exist_ok=True)

def load_settings():
    settings_file = CONFIG / "settings.json"
    if settings_file.exists():
        return json.loads(settings_file.read_text())
    return default_settings()

def save_settings(settings):
    CONFIG / "settings.json".write_text(json.dumps(settings, indent=2))
```

## Persistência
- Todos os dados armazenados localmente
- Não requer banco de dados
- Formato JSON para configurações
- Arquivos de áudio em WAV/FLAC

## Cleanup
-定期 cleanup de arquivos antigos (opcional)
- Manter controle de espaço em disco
- Compressão de transcrições velhas