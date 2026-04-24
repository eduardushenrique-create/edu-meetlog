## Descrição
Implementar atalhos de teclado (hotkeys) para controle rápido.

## Atalhos
| Atalho | Ação |
|--------|------|
| CTRL + ALT + R | Start/Stop gravação |
| CTRL + ALT + S | Abrir/focar aplicação |

## Implementação (Tauri)
```rust
// src-tauri/src/main.rs
use tauri::{AppHandle, Manager, Emitter};
use tauri_hotkey::{HotKey, HotKeyManager, Modifiers};

fn setup_hotkeys(app: &AppHandle) {
    let mut manager = HotKeyManager::new(app);
    
    // CTRL + ALT + R → Toggle recording
    let r_hotkey = HotKey::new(Some(Modifiers::CONTROL | Modifiers::ALT), "r");
    manager.register(r_hotkey, move |_app, _hotkey| {
        // Emit event para toggle recording
        app.emit("toggle-recording", ());
    }).unwrap();
    
    // CTRL + ALT + S → Show/focus app
    let s_hotkey = HotKey::new(Some(Modifiers::CONTROL | Modifiers::ALT), "s");
    manager.register(s_hotkey, move |app, _hotkey| {
        // Mostrar e focar janela
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
        }
    }).unwrap();
}
```

## Implementação (React)
```tsx
import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';

useEffect(() => {
  const unlisten = await listen('toggle-recording', () => {
    setRecording(!recording);
  });
  
  return () => unlisten();
}, []);
```

## Configuração tauri.conf.json
```json
{
  "app": {
    "windows": [
      {
        "title": "Edu MeetLog",
        "width": 800,
        "height": 600,
        "resizable": true,
        "fullscreen": false
      }
    ]
  }
}
```

## Notas
- Hotkeys funcionam mesmo com app minimizado
- Mostrar notificação ao acionar
- Permitir configurar hotkeys nas settings (avançado)