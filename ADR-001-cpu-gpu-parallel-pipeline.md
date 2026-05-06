# ADR-001: Paralelismo CPU/GPU no Pipeline de Transcrição em Tempo Real

**Status:** Accepted  
**Data:** 2026-05-05  
**Deciders:** Eduardo (mantenedor)

---

## Context

O pipeline de transcrição em tempo real anterior tinha um gargalo estrutural:
uma única thread processava chunks de microfone e sistema **sequencialmente**,
chamando `model.transcribe()` (bloqueante, GPU) antes de processar o próximo chunk.

```
Antes (por ciclo de 200ms, 1 thread):
  MIC:    [_trim_silence CPU ──► model.transcribe GPU wait] →
          [_trim_silence CPU ──► model.transcribe GPU wait] → ...
  SYSTEM: (só começa depois que todos os chunks de MIC terminam)
          [_trim_silence CPU ──► model.transcribe GPU wait] → ...
```

- `beam_size=5` para real-time (mesmo valor do batch) — penaliza latência sem benefício perceptível
- Batch workers carregavam instâncias separadas do WhisperModel mesmo quando o modelo já estava carregado

---

## Decision

Adotar arquitetura **Pipeline CPU/GPU com fontes paralelas**:

1. **Duas threads CPU** (uma por fonte: `rt-cpu-mic`, `rt-cpu-system`) executam `_trim_silence` + enfileiram audio pré-processado
2. **Uma thread GPU** (`InferencePipeline._gpu_worker`) drena a fila e chama `model.transcribe()` exclusivamente
3. **`beam_size=1`** para real-time (configurável via `beam_size_realtime` em settings)
4. **Modelo compartilhado** entre real-time e batch workers (sem duplicação de VRAM)

```
Depois:
  Thread rt-cpu-mic:    [_trim_silence] → queue →
  Thread rt-cpu-system: [_trim_silence] → queue →  GPU Thread: [transcribe] → callback → merge → broadcast
  (ambas em paralelo)                              (único consumer, processa fila continuamente)
```

---

## Arquivos Modificados

| Arquivo | Mudança |
|---|---|
| `backend/realtime_transcriber.py` | Nova classe `InferencePipeline` com fila + GPU worker; `RealtimeTranscriber` vira wrapper; `submit_chunk()` para path async |
| `backend/main.py` | `_cpu_source_worker()` por fonte; `_realtime_coordinator()` que lança 2 threads; `_on_segments_received()` callback; `Settings` com `beam_size_realtime` e `beam_size_batch`; `shared_model` passado do `model_cache` do queue_worker |
| `backend/queue_worker.py` | `transcribe_audio()` aceita `beam_size`; `_load_beam_size_batch()` lê de settings; `process_file()` passa beam_size correto |

---

## Configurações Expostas

```json
{
  "beam_size_realtime": 1,
  "beam_size_batch": 5
}
```

- `beam_size_realtime=1`: Máxima velocidade para transcrição ao vivo. Qualidade ainda boa para PT-BR.
- `beam_size_batch=5`: Qualidade máxima para transcrições de gravações finalizadas.

---

## Ganho Esperado

| Cenário | Antes | Depois |
|---|---|---|
| Latência por chunk (GPU float16) | 0.8–1.5s | **0.2–0.4s** |
| Latência por chunk (CPU int8) | 2–4s | 0.8–1.5s |
| Utilização GPU durante gravação | ~40% | ~80–90% |
| VRAM usada (large-v3) | 2× se batch + RT ativos | **1× compartilhado** |

---

## Constraints

- App permanece **100% local** — nenhum serviço externo adicionado
- GPU com <4GB VRAM: `large-v3` pode não caber; usar `medium` ou `base` via Settings
- `InferencePipeline.submit()` tem `maxsize=12`; se GPU não acompanhar o áudio, o chunk mais antigo é descartado (backpressure)

---

## Próximos Itens (fora do escopo deste ADR)

- [ ] Expor `beam_size_realtime` na UI (painel Settings)
- [ ] Métricas de latência por chunk no painel de Status
- [ ] Testar com modelo `medium` em CPU-only para comparação de latência
