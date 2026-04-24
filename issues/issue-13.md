## Descrição
Testar operação contínua por 4-5 horas diárias sem interrupções ou vazamentos de memória.

## Objetivos
- [ ] Teste de estresse de 4+ horas
- [ ] Monitorar uso de memória
- [ ] Verificar estabilidade de gravação
- [ ] Verificar estabilidade de transcrição
- [ ] Detectar e corrigir vazamentos

## Cenários de teste
| Cenário | Duração | Verificações |
|--------|---------|-------------|
| Gravação contínua | 4h | Sem perda de áudio |
| Múltiplas sessões | 5 dias | Estado persiste |
|many transcrições | 10+ | Fila processa tudo |
| Idle prolongado | 8h | Sem crash |

## Monitoramento
- Uso de CPU (target: <50%)
- Uso de memória (target: <2GB)
- Espaço em disco
- Temperatura (se possível)

## Logs a verificar
```
- Gravação: inicio/fim de cada segmento
- Transcrição: inicio/fim de cada arquivo
- Erros: exceptions e stack traces
- Recursos: CPU, MEM, DISK
```

## Checklist de verificação
- [ ] Sem perda de segmentos de áudio
- [ ] Sem arquivos corrompidos
- [ ] Transcrições completas
- [ ] Memória estável (sem leak)
- [ ] CPU within limits
- [ ] UI responsiva durante operação

## Scripts de teste
```python
import psutil
import time

def monitor_resources():
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        print(f"CPU: {cpu}% | MEM: {mem}%")
        time.sleep(60)

# Executar em paralelo com gravação
```

## Métricas de sucesso
- 0 crashes em 4h
- <1% perda de áudio
- <80% memória média
- <50% CPU média