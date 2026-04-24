## Descrição
Criar backend FastAPI com endpoints REST para controle de gravação.

## Endpoints
| Método | Path | Descrição |
|--------|------|-----------|
| POST | /recording/start | Iniciar gravação |
| POST | /recording/stop | Parar gravação |
| GET | /status | Status atual da aplicação |

## Request/Response

### POST /recording/start
```json
{
  "mic_enabled": true,
  "system_enabled": true,
  "segment_duration": 300
}
```

### POST /recording/stop
```json
{
  "success": true,
  "message": "Recording stopped",
  "duration": 3600
}
```

### GET /status
```json
{
  "state": "IDLE|RECORDING|PROCESSING|ERROR",
  "recording_duration": 3600,
  "mic_enabled": true,
  "system_enabled": true,
  "queue_stats": {
    "pending": 5,
    "processing": 2,
    "done": 10,
    "failed": 1
  }
}
```

## Estados
- **IDLE**: Aplicação parada
- **RECORDING**: Gravando áudio
- **PROCESSING**: Processando transcrição
- **ERROR**: Erro occurred

## Implementação
- Usar FastAPI com Python
- Implementar como processo separado ou embedado no Tauri
- Comunicar via IPC ou HTTP interno

## Código base
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RecordingRequest(BaseModel):
    mic_enabled: bool = True
    system_enabled: bool = True

@app.post("/recording/start")
def start_recording(req: RecordingRequest):
    # Iniciar captura de áudio
    pass

@app.post("/recording/stop")
def stop_recording():
    # Parar captura de áudio
    pass

@app.get("/status")
def get_status():
    # Retornar status atual
    pass
```

## Referências
- https://fastapi.tiangolo.com/