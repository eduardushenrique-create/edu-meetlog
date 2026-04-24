## Descrição
Implementar segmentação de áudio em pacotes de 5 minutos com sincronização por timestamp.

## Objetivos
- [ ] Segmentar áudio a cada 5 minutos
- [ ] Manter sincronização por timestamp entre microfone e sistema
- [ ] Nomear arquivos com timestamp de início
- [ ] Armazenar metadados da gravação

## Especificações
- **Duração do segmento**: 5 minutos (300 segundos)
- **Formato de saída**: WAV ou FLAC
- **Taxa de amostragem**: 16kHz
- **Canais**: Mono

## Estrutura de arquivos
```
recordings/
├── 2024-01-15_143000_mic.wav
├── 2024-01-15_143000_sys.wav
├── 2024-01-15_143000_meta.json
├── 2024-01-15_143500_mic.wav
└── ...
```

## Metadados (meta.json)
```json
{
  "start": "2024-01-15T14:30:00Z",
  "end": "2024-01-15T14:35:00Z",
  "source": "mic|system",
  "duration": 300.0,
  "sample_rate": 16000
}
```

## Lógica de segmentação
1. Iniciar timer quando gravação começar
2. Após 5 minutos, fechar arquivo atual e criar novo
3. Continuar gravando sem interrupção
4. Usar timestamp UTC para nomeação

## Buffer e performance
- Usar buffer de streaming para evitar memory leaks
- Gravar diretamente em disco (não em memória)
- Limitar número de arquivos abertos