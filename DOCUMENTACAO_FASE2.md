# 📄 DOCUMENTAÇÃO OFICIAL CONSOLIDADA — EDU MEETLOG

## FASE 2 — PROCESSAMENTO INTELIGENTE, AUTOMAÇÃO, DIARIZAÇÃO E POPUPS CONTEXTUAIS

Versão: 2.3 (Final consolidada + detalhamento técnico de execução)

---

### 1. CONTEXTO

#### 1.1 Evolução da Fase 2

Esta versão adiciona:
- Sistema de popup discreto inteligente
- Especificação técnica detalhada de implementação (nível executor)
- Estratégias concretas de detecção de reunião (OS + áudio)
- Detalhamento de cada tarefa com como implementar

---

### 2. ESCOPO FINAL DA FASE 2

Inclui:
- Realtime transcription
- GPU acceleration
- Meeting detection
- Smart popup (UX proativa)
- Priority queue
- Context awareness
- Diarização (pós-processamento)

---

### 3. ARQUITETURA FINAL

```
[Audio Capture]
   ↓
[VAD Engine]
   ↓
[Meeting Detection Engine]
   ↓
[Popup System]
   ↓
[Chunk Buffer (3–5s)]
   ↓
[Realtime Queue]
   ↓
[GPU/CPU Inference]
   ↓
[Streaming UI]
   ↓
[Storage]
   ↓
[Diarization Worker]
   ↓
[Alignment Engine]
```

---

### 4. SMART POPUP SYSTEM (ATUALIZAÇÃO CRÍTICA)

#### 4.1 Comportamento UX

**Características obrigatórias:**
- Posição: top-right da tela
- Estilo: discreto (toast)
- Duração: 30 segundos
- Auto-dismiss: obrigatório
- Não bloqueante
- Sempre acima de outras janelas (overlay leve)

#### 4.2 Estados

**Popup de início:**
- Trigger: `meeting_start_detected`
- Conteúdo: "Reunião detectada"
- Botões: Iniciar gravação | Ignorar

**Popup de término:**
- Trigger: `meeting_end_detected`
- Conteúdo: "Reunião finalizada?"
- Botões: Parar gravação | Continuar

#### 4.3 Regras
- Fecha automaticamente após 30s
- Se ignorado: segue configuração (auto-start / auto-stop)

#### 4.4 Implementação técnica (Tauri)

**Tarefa F2-T37 — Popup system**

Tecnologias:
- Tauri window API
- React (UI layer)
- Tailwind (estilo)

**Passo a passo:**
1. Criar janela overlay no Tauri:
```javascript
import { WebviewWindow } from '@tauri-apps/api/window';

const popup = new WebviewWindow('popup', {
  width: 320,
  height: 100,
  decorations: false,
  alwaysOnTop: true,
  transparent: true,
});
```
2. Posicionar no canto superior direito
3. Obter resolução da tela
4. Offset fixo (ex: 20px)
5. Implementar auto-dismiss: `setTimeout(() => popup.close(), 30000);`
6. Comunicação com backend via events (Tauri emit/listen)
7. Garantir não bloqueio da UI principal

---

### 5. MEETING DETECTION ENGINE (DETALHADO)

#### F2-T1 — VAD

**Tecnologia:** webrtcvad (Python)

**Passos:**
1. Capturar áudio raw (16kHz mono)
2. Dividir em frames (20ms)
3. Aplicar VAD: `vad.is_speech(frame, sample_rate)`
4. Emitir eventos contínuos

#### F2-T2 — Detector de início

**Passos:**
1. Manter buffer temporal (fila circular)
2. Contar frames de fala contínua
3. Se > threshold: emitir evento

#### F2-T3 — Detector de término

**Passos:**
1. Monitorar ausência de fala
2. Se silêncio contínuo > threshold: trigger

#### F2-T4 — Monitor de processos

**Tecnologia:** Python: psutil (cross-platform)

**Passos:**
1. Listar processos ativos:
```python
import psutil
for proc in psutil.process_iter(['name']):
```
2. Match com: zoom.exe, teams.exe, chrome (com heurística futura)
3. Emitir eventos

**Estratégia híbrida (IMPORTANTE):**
- Detecção final = combinação: (Audio VAD) + (Process detection)

---

### 6. REALTIME TRANSCRIPTION ENGINE

#### F2-T8 — Chunking

**Passos:**
1. Criar buffer circular
2. Agrupar 3–5 segundos
3. Garantir timestamps contínuos

#### F2-T9 — Streaming

**Tecnologia:** faster-whisper

**Passos:**
1. Receber chunk
2. Enviar para inferência
3. Emitir partial + final

#### F2-T10 — WebSocket

**Tecnologia:** FastAPI

**Implementação:**
```python
@app.websocket("/stream/transcription")
```

---

### 7. GPU ACCELERATION

#### F2-T11 — Detectar GPU

**Tecnologia:** torch.cuda

**Implementação:** `torch.cuda.is_available()`

#### F2-T12 — Configurar Whisper

```python
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
```

#### F2-T13 — Worker pool

**Estratégia:**
- CPU cores → threads
- GPU → batch size

#### F2-T14 — Scheduler

**Implementação:** Queue manager com prioridade e distribuição

---

### 8. PRIORITY QUEUE SYSTEM

#### F2-T15 — Implementação

**Tecnologia:** asyncio.Queue ou Redis (opcional)

**Passos:**
1. Criar múltiplas filas
2. Priorizar realtime

#### F2-T16 — Backpressure

**Estratégia:** Limite de itens, drop oldest

---

### 9. DIARIZATION ENGINE (DETALHADO)

#### F2-T24 — Integração

**Tecnologia:** pyannote.audio

**Passos:**
1. Carregar modelo
2. Processar áudio completo
3. Gerar segmentos

#### F2-T26 — Alignment

**Estratégia:** Overlap temporal

**Passos:**
1. Para cada segmento Whisper
2. Encontrar speaker com maior interseção
3. Atribuir speaker

---

### 10. CONTEXT AWARENESS

#### F2-T17 — Monitor de áudio

**Passos:**
1. Monitorar volume RMS
2. Detectar atividade

#### F2-T18 — Calendar stub

Interface pronta (não implementar integração ainda)

---

### 11. UI — IMPLEMENTAÇÃO

#### F2-T21 — Realtime transcript

**Passos:**
1. Conectar WebSocket
2. Atualizar estado React
3. Render incremental

#### F2-T33 — Speakers

**Passos:**
1. Mapear speaker → cor
2. Atualizar UI

---

### 12. SETTINGS

#### F2-T23 / F2-T36

**Implementação:** Persistência local (JSON / SQLite)

---

### 13. EDGE CASES (DETALHADO)

#### F2-E1 — TV/música

**Mitigação futura:** Classificação de áudio

#### F2-E4 — Sobreposição

**Estratégia:** Escolher maior energia

---

### 14. CRITÉRIOS DE ACEITAÇÃO

- Latência < 2s
- Popup aparece corretamente
- Popup fecha após 30s
- Não bloqueia UI
- GPU utilizada quando disponível
- Diarização funcional
- Sistema estável por 5h

---

### 15. DECISÕES ARQUITETURAIS

- Popup = não intrusivo
- Diarização = pós-processamento
- GPU = opcional
- Pipeline desacoplado

---

### 16. DIRETRIZES PARA EXECUÇÃO

**Ordem recomendada:**
1. GPU + realtime
2. VAD + detection
3. Popup system
4. Queue system
5. Diarization
6. UI refinements

---

### 17. PREPARAÇÃO PARA FASE 3

- LLM local
- Insights automáticos
- Tasks extraction
- Speaker identification

---

## TAREFAS DA FASE 2 (LISTAGEM)

| ID | Tarefa | Descrição |
|----|---------|------------|
| F2-T1 | VAD | Implementar Voice Activity Detection com webrtcvad |
| F2-T2 | Detector de início | Detectar início de fala contínua |
| F2-T3 | Detector de término | Detectar fim de reunião por silêncio |
| F2-T4 | Monitor de processos | Monitorar processos (Zoom, Teams, Chrome) |
| F2-T8 | Chunking | Buffer circular para chunks de 3-5s |
| F2-T9 | Streaming | Streaming de transcrição com faster-whisper |
| F2-T10 | WebSocket | Endpoint WebSocket para streaming |
| F2-T11 | Detectar GPU | Detectar disponibilidade de GPU CUDA |
| F2-T12 | Configurar Whisper GPU | Configurar Whisper para GPU |
| F2-T13 | Worker pool | Pool de workers para GPU/CPU |
| F2-T14 | Scheduler | Scheduler com prioridades |
| F2-T15 | Priority queue | Sistema de filas com prioridade |
| F2-T16 | Backpressure | Controle de pressão na fila |
| F2-T17 | Monitor de áudio | Monitorar volume RMS |
| F2-T18 | Calendar stub | Interface para calendário |
| F2-T21 | Realtime transcript UI | UI de transcrição em tempo real |
| F2-T23 | Settings persistência | Persistir configurações |
| F2-T24 | Diarization | Integração com pyannote.audio |
| F2-T26 | Alignment | Alinhamento de speakers |
| F2-T33 | Speakers UI | UI para exibir speakers |
| F2-T36 | Settings UI | Interface de configurações |
| F2-T37 | Popup system | Sistema de popups inteligentes |

---

## HISTÓRICO DE VERSÕES

- **v1.0** - Fase 1: Captura básica de áudio
- **v2.0** - Fase 2: Processamento inteligente e popups (em desenvolvimento)
- **v2.3** - Fase 2 com detalhamento técnico completo
