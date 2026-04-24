## Descrição
Implementar sistema de fila de processamento para transcrição assíncrona.

## Estrutura de diretórios
```
queue/
├── pending/      # Arquivos aguardando processamento
├── processing/  # Arquivos sendo processados
├── done/        # Processados com sucesso
└── failed/      # Falhas no processamento
```

## Configuração
- **Workers**: 2 (processos paralelos)
- **Retry**: Até 3x em caso de falha
- **Intervalo de verificação**: 5 segundos

## Fluxo
1. Arquivo criado em `recordings/`
2. Mover para `queue/pending/`
3. Worker pega arquivo → move para `processing/`
4. Processa transcrição
5. Se sucesso → move para `done/`, se falha → `failed/`

## Metadados do arquivo na fila
```json
{
  "id": "uuid",
  "filename": "2024-01-15_143000_mic.wav",
  "attempts": 0,
  "max_attempts": 3,
  "status": "pending|processing|done|failed",
  "created_at": "2024-01-15T14:30:00Z",
  "error": null
}
```

## Implementação Python
```python
import os
import shutil
import time
from pathlib import Path
from threading import Thread

QUEUE_DIR = Path("queue")
PENDING = QUEUE_DIR / "pending"
PROCESSING = QUEUE_DIR / "processing"
DONE = QUEUE_DIR / "done"
FAILED = QUEUE_DIR / "failed"

def worker():
    while True:
        files = list(PENDING.glob("*.wav"))
        for f in files:
            # Mover para processing
            f.rename(PROCESSING / f.name)
            # Processar
            try:
                transcribe(f)
                (PROCESSING / f.name).rename(DONE / f.name)
            except:
                (PROCESSING / f.name).rename(FAILED / f.name)
        time.sleep(5)

# Iniciar 2 workers
for _ in range(2):
    Thread(target=worker, daemon=True).start()
```

## Retry logic
- Contador de tentativas no arquivo .meta.json
- Após 3 falhas, mover para failed/
- Registrar erro em log