## Descrição
Criar interface do Dashboard com status, timer, botão Start/Stop e info da fila.

## Componentes
| Componente | Descrição |
|------------|-----------|
| Status | Displays "Recording" or "Stopped" |
| Timer | Tempo transcorrido desde o início |
| Botão Start/Stop | Inicia/para gravação |
| Queue Info | Número de arquivos em cada status |

## Layout
```
┌─────────────────────────────────────────┐
│  ┌──────┐                             │
│  │ 📁  │  Edu MeetLog               │
│  └──────┘                             │
├─────────────────────────────────────────┤
│  Dashboard  Meetings  Transcription   │
│  Settings                              │
├─────────────────────────────────────────┤
│                                         │
│         STATUS: Recording              │
│              02:34:57                   │
│                                         │
│         [  INICIAR  ]                   │
│                                         │
│   Fila:                                 │
│   └ Pendentes: 3                        │
│   └ Processando: 1                     │
│   └ Concluídos: 12                      │
│                                         │
└─────────────────────────────────────────┘
```

## Implementação React
```tsx
import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [recording, setRecording] = useState(false);
  const [timer, setTimer] = useState(0);
  const [queue, setQueue] = useState({ pending: 0, processing: 0, done: 0 });

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (recording) {
      interval = setInterval(() => {
        setTimer(t => t + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [recording]);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-6">
      <div className="text-2xl mb-4">
        STATUS: {recording ? 'Recording' : 'Stopped'}
      </div>
      <div className="text-4xl mb-6">{formatTime(timer)}</div>
      <button
        onClick={() => setRecording(!recording)}
        className="px-6 py-3 bg-blue-600 rounded"
      >
        {recording ? 'Stop' : 'Start'}
      </button>
    </div>
  );
}
```

## Integração com API
- Fetch status via GET /status
- Enviar comandos via POST /recording/start e POST /recording/stop
- Polling a cada 5 segundos para atualizar queue