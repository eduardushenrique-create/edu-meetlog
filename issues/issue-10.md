## Descrição
Criar interface de transcrição com formato: [timestamp] SPEAKER: texto

## Objetivos
- [ ] Exibir transcrição formatada
- [ ] Mostrar speaker (USER/OTHER)
- [ ] Mostrar timestamps
- [ ] Permitir scroll e busca

## Layout
```
┌─────────────────────────────────────────┐
│  TRANSCRIPTION              [← Voltar]    │
├─────────────────────────────────────────┤
│                                         │
│  [00:00] USER: Olá, bom dia!            │
│  [00:03] OTHER: Bom dia! Tudo bem?      │
│  [00:05] USER: Tudo bem, e você?       │
│  [00:08] OTHER: Muito bem!             │
│                                         │
│  [00:10] USER: Vamos começar a        │
│            reunião.                    │
│                                         │
│  ...                                   │
│                                         │
└─────────────────────────────────────────┘
```

## Formato JSON de entrada
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

## Implementação React
```tsx
interface Segment {
  id: number;
  start: number;
  end: number;
  speaker: 'user' | 'other';
  text: string;
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `[${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}]`;
}

export default function Transcription({ segments }: { segments: Segment[] }) {
  return (
    <div className="p-6 font-mono">
      <h1 className="text-2xl mb-4">TRANSCRIPTION</h1>
      <div className="space-y-2">
        {segments.map(seg => (
          <div key={seg.id}>
            <span className="text-gray-400">
              {formatTimestamp(seg.start)}
            </span>{' '}
            <span className={seg.speaker === 'user' ? 'text-green-400' : 'text-blue-400'}>
              {seg.speaker.toUpperCase()}:
            </span>{' '}
            {seg.text}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Features adicionais
- Busca por texto
- Copiar transcrição
- Exportar como TXT/PDF