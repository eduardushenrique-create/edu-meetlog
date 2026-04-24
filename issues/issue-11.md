## Descrição
Criar interface de configurações com opções de personalização.

## Objetivos
- [ ] Toggle para microfone ON/OFF
- [ ] Toggle para sistema ON/OFF
- [ ] Seleção de modelo Whisper
- [ ] Número de workers
- [ ] Auto-start ao iniciar app

## Layout
```
┌─────────────────────────────────────────┐
│  SETTINGS                              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Captura de Áudio                 │   │
│  │ ├─ 🎤 Microfone    [ON]         │   │
│  │ └─ 🔊 Sistema      [OFF]        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Transcrição                      │   │
│  │ ├─ Modelo:            [large-v3]│   │
│  │ └─ Workers:           [2]       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Inicialização                   │   │
│  │ └─ Auto-start ao iniciar [OFF]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│            [SALVAR]                      │
│                                         │
└─────────────────────────────────────────┘
```

## Componentes
| Campo | Tipo | Padrão |
|-------|------|--------|
| mic_enabled | Toggle | true |
| system_enabled | Toggle | false |
| model | Select | large-v3 |
| workers | Number | 2 |
| auto_start | Toggle | false |

## Modelos disponíveis
- tiny
- base
- small
- medium
- large-v2
- large-v3

## Implementação React
```tsx
import { useState } from 'react';

interface Settings {
  mic_enabled: boolean;
  system_enabled: boolean;
  model: string;
  workers: number;
  auto_start: boolean;
}

export default function Settings() {
  const [settings, setSettings] = useState<Settings>({
    mic_enabled: true,
    system_enabled: false,
    model: 'large-v3',
    workers: 2,
    auto_start: false
  });

  const save = async () => {
    await fetch('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl">SETTINGS</h1>
      
      <div className="space-y-2">
        <label className="flex items-center justify-between">
          <span>Microfone</span>
          <input
            type="checkbox"
            checked={settings.mic_enabled}
            onChange={e => setSettings({...settings, mic_enabled: e.target.checked})}
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>Sistema</span>
          <input
            type="checkbox"
            checked={settings.system_enabled}
            onChange={e => setSettings({...settings, system_enabled: e.target.checked})}
          />
        </label>
      </div>

      <select
        value={settings.model}
        onChange={e => setSettings({...settings, model: e.target.value})}
      >
        <option value="tiny">tiny</option>
        <option value="base">base</option>
        <option value="small">small</option>
        <option value="medium">medium</option>
        <option value="large-v2">large-v2</option>
        <option value="large-v3">large-v3</option>
      </select>

      <input
        type="number"
        value={settings.workers}
        onChange={e => setSettings({...settings, workers: parseInt(e.target.value)})}
      />

      <button onClick={save} className="px-6 py-2 bg-blue-600 rounded">
        SALVAR
      </button>
    </div>
  );
}
```