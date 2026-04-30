# Edu MeetLog - Documentação da Fase 3

A Fase 3 do Edu MeetLog focou em expandir as capacidades de gestão, organização e governança das transcrições processadas. A seguir, detalhamos a arquitetura técnica e os endpoints implementados nesta fase.

## 1. Gestão de Transcrições (Bulk Actions)

Foram introduzidas ações em lote para permitir que o usuário limpe ou arquive transcrições antigas com segurança.

### 1.1. Arquivamento Seguro
- **Campo:** O estado de arquivamento é persistido no arquivo `config/meetings.json` através do atributo booleano `archived: true`.
- **Comportamento UI:** Transcrições arquivadas não aparecem na listagem principal de "Transcrições", mas podem ser visualizadas alterando o filtro para "Arquivadas".
- **Endpoint:** `POST /meetings/bulk-archive` (Espera payload `{"ids": ["id1", "id2"]}`).

### 1.2. Exclusão em Lote
- **Comportamento:** Atualmente o sistema utiliza uma exclusão "hard" definitiva, removendo as entradas no `meetings.json` e todos os arquivos físicos em disco local (`.wav` ou `.json`) associados ao ID da reunião.
- **Endpoint:** `POST /meetings/bulk-delete` (Espera payload `{"ids": ["id1", "id2"]}`).

---

## 2. Rótulos e Etiquetas (Labels)

Um sistema de categorização manual e automático de reuniões foi introduzido.

### 2.1. Entidade
Os rótulos são salvos no arquivo `config/labels.json` possuindo o esquema:
- `id`: string (UUID ou slug)
- `name`: string
- `color`: string (Hex)

As reuniões passam a conter um array `labels` e `suggested_labels` contendo os IDs das etiquetas associadas.

### 2.2. Endpoints de Gerenciamento
- `GET /labels` - Lista todas as etiquetas.
- `POST /labels` - Cria uma nova etiqueta.
- `DELETE /labels/{label_id}` - Exclui uma etiqueta.
- `POST /meetings/{meeting_id}/labels` - Sobrescreve as etiquetas atribuídas a uma transcrição (Payload: `{"label_ids": [...]}`).

---

## 3. Sugestão por Inteligência Artificial

A aplicação agora analisa o texto transcrito para sugerir rótulos.

### 3.1. Estratégia Implementada
O `ai_engine.py` utiliza agora **Zero-Shot Context Classification** (classificação semântica em português) processada 100% off-line usando o modelo `mDeBERTa-v3` via biblioteca `transformers`.
- Se a biblioteca não estiver instalada (ou houver erro no carregamento), o sistema possui um "fallback seguro" utilizando regex/palavras-chave determinísticas de forma transparente ao usuário.
- O limiar de confiança do modelo está calibrado em 65%.
- As sugestões são salvas na propriedade `suggested_labels` do `meetings.json` imediatamente após o fim do processamento do `queue_worker.py`.
- O usuário é notificado via UI com botões amigáveis ("✓ Aceitar" e "✕ Recusar") para endossar ou rejeitar o contexto da IA.
- **Endpoint:** `POST /meetings/{meeting_id}/suggest-labels` permite re-calcular ou forçar uma nova sugestão com base nos novos rótulos criados.

---

## 4. Segurança e Auditoria

Um log de auditoria foi instituído para manter a rastreabilidade das ações do usuário.

### 4.1. Audit Log
Toda ação crítica interage com `backend/audit_log.py`, que adiciona registros no `config/audit.json`.
Eventos monitorados:
- `CREATE_LABEL`
- `DELETE_LABEL`
- `UPDATE_MEETING_LABELS`
- `BULK_DELETE_MEETINGS`
- `BULK_ARCHIVE_MEETINGS`

O payload possui `timestamp`, `action` e `details`.

---

# Checklist de Release (Fase 3)

## Funcionalidades (Backend)
- [x] O arquivo `meetings.json` suporta chaves `archived`, `labels` e `suggested_labels`.
- [x] Rota `/meetings/bulk-delete` remove transcrições selecionadas e apaga arquivos do disco local.
- [x] Rota `/meetings/bulk-archive` arquiva transcrições selecionadas.
- [x] Rota `/labels` cadastra, lista e deleta etiquetas no `labels.json`.
- [x] Script `ai_engine.py` retorna rótulos adequados baseados nas transcrições (fallback para keyword-matching implementado).
- [x] Pipeline no `queue_worker.py` roda as sugestões de IA automaticamente no fim da etapa de *merge*.
- [x] O `audit_log.py` intercepta e salva logs de segurança.

## Funcionalidades (Frontend/UI)
- [x] Na aba "Meetings", há *checkboxes* para a seleção múltipla.
- [x] Barra flutuante de ações aparece após a primeira seleção (Excluir/Arquivar).
- [x] Confirmações visuais (`window.confirm`) antecedem o arquivo e exclusão de transcrições.
- [x] Incluído botão global de "Selecionar Tudo" na listagem de reuniões.
- [x] Menu *dropdown* permite filtrar "Ativas" e "Arquivadas" e também selecionar visualização por um rótulo específico.
- [x] Tela da "Transcrições" renderiza "badges" para cada etiqueta aceita.
- [x] Tela da "Transcrições" mostra *box* de sugestões de IA otimizado com espaçamento legível ("✓ Aceitar" e "✕ Recusar").
- [x] Corrigido o design dos controles de janela nativos do Windows ("DarkWindow").
- [x] Na aba de configurações ("Settings"), existe o CRUD para registrar Novas Etiquetas.
- [x] Tela da "Transcrições" permite incluir uma etiqueta manualmente em um *dropdown*.
