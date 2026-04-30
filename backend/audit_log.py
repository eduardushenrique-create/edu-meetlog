import json
import time
from datetime import datetime
from pathlib import Path
from paths import CONFIG_DIR

AUDIT_FILE = CONFIG_DIR / "audit.json"

def log_audit_event(action: str, details: dict):
    """
    Registra eventos de auditoria (ex: arquivamento, exclusão)
    conforme especificado na F3.5.2 do Roadmap.
    """
    try:
        events = []
        if AUDIT_FILE.exists():
            try:
                events = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        event = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            # Se houvesse auth, colocaríamos "user_id" aqui
            "user": "system_local" 
        }
        events.append(event)
        AUDIT_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Erro ao salvar log de auditoria: {e}")
