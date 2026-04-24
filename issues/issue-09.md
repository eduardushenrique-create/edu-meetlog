## Descrição
Criar interface Meetings com lista de reuniões e funcionalidade de abrir ao clicar.

## Objetivos
- [ ] Listar todas as gravações realizadas
- [ ] Ordenar por data (mais recente primeiro)
- [ ] Mostrar metadata (duração, data, status)
- [ ] Ao clicar, abrir transcrição

## Layout
```
┌─────────────────────────────────────────┐
│  MEETINGS                    [← Voltar]  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📅 15/01/2024 - 14:30          │   │
│  │    Duração: 1h 23min           │   │
│  │    Status: Transcrito ✓        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📅 15/01/2024 - 10:00           │   │
│  │    Duração: 45min               │   │
│  │    Status: Pendente             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📅 14/01/2024 - 16:30           │   │
│  │    Duração: 2h 10min            │   │
│  │    Status: Erro                 │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## Implementação
```tsx
import { useState, useEffect } from 'react';

interface Meeting {
  id: string;
  date: string;
  duration: number;
  status: 'pending' | 'processing' | 'done' | 'failed';
}

export default function Meetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);

  useEffect(() => {
    // Fetch meetings da API ou sistema de arquivos
    fetch('/api/meetings')
      .then(res => res.json())
      .then(setMeetings);
  }, []);

  const openMeeting = (id: string) => {
    // Navegar para TRANSCRIPTION com o meeting ID
    window.location.href = `/transcription/${id}`;
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">MEETINGS</h1>
      <div className="space-y-3">
        {meetings.map(meeting => (
          <div
            key={meeting.id}
            onClick={() => openMeeting(meeting.id)}
            className="p-4 border rounded cursor-pointer hover:bg-gray-800"
          >
            <div className="font-bold">{meeting.date}</div>
            <div>Duração: {formatDuration(meeting.duration)}</div>
            <div>Status: {meeting.status}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Fonte de dados
- Ler diretório recordings/
- Agrupar por sessão ( timestamp )
- Verificar existência de transcript correspondente