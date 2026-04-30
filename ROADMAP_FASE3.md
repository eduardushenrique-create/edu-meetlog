# Fase 3 — Gestão de Transcrições Processadas e Rótulos

## Objetivo da fase 3

Adicionar ao aplicativo recursos para:

1. Selecionar transcrições/reuniões já processadas.
2. Arquivar transcrições processadas sem removê-las definitivamente.
3. Excluir transcrições processadas de forma segura.
4. Cadastrar e administrar rótulos reutilizáveis para clientes, assuntos ou outros agrupadores.
5. Atribuir rótulos manualmente a uma reunião/transcrição.
6. Sugerir rótulos automaticamente com base no conteúdo da transcrição.

## Premissas de arquitetura

- Manter a separação atual entre interface, rotas/controllers, serviços/use cases, camada de persistência/repositories e pipeline de processamento/IA.
- Evitar acoplar a sugestão de rótulos diretamente à tela; a sugestão deve ficar em um serviço próprio, reutilizável pelo processamento automático e por acionamento manual.
- Não reprocessar áudio nem transcrição para arquivar, excluir ou rotular registros já processados.
- Arquivamento deve ocultar a transcrição da listagem padrão, mas manter o registro recuperável.
- Exclusão deve respeitar o padrão atual do aplicativo. Quando não houver exclusão definitiva já padronizada, usar exclusão lógica com `deleted_at`.
- Rótulos devem ser entidades próprias e reutilizáveis, com relacionamento muitos-para-muitos com reuniões/transcrições.
- Sugestões automáticas devem ser revisáveis pelo usuário antes de serem aplicadas como rótulos definitivos.

---

## Épico F3.1 — Modelo de dados e persistência

### F3.1.1 — Mapear entidades atuais de reunião/transcrição

**Descrição:** Identificar no projeto qual entidade representa a reunião e qual entidade representa a transcrição processada.

**Tarefas:**

- Localizar o modelo/tabela atual de reuniões/transcrições.
- Confirmar o campo que indica que uma transcrição está processada.
- Confirmar o padrão atual de timestamps, status, soft delete e auditoria.
- Documentar se a nova relação de rótulos será feita com `meeting_id`, `transcription_id` ou equivalente existente.

**Critérios de aceite:**

- A implementação usa os modelos existentes sem duplicar entidades.
- As novas colunas e tabelas seguem o padrão de nomenclatura do projeto.

### F3.1.2 — Criar suporte de arquivamento para transcrições processadas

**Descrição:** Adicionar persistência para marcar transcrições/reuniões como arquivadas.

**Tarefas:**

- Adicionar campo `archived_at` ou status equivalente conforme padrão atual.
- Adicionar `archived_by` se o projeto já possuir autenticação/usuários.
- Criar índice para listagem por status de processamento e arquivamento.
- Garantir que a listagem padrão ignore registros arquivados.

**Critérios de aceite:**

- Transcrições arquivadas não aparecem na listagem padrão.
- Transcrições arquivadas podem ser consultadas por filtro específico.
- O conteúdo da transcrição permanece preservado após arquivamento.

### F3.1.3 — Criar suporte de exclusão segura

**Descrição:** Permitir exclusão de transcrições processadas seguindo o padrão de segurança do aplicativo.

**Tarefas:**

- Usar exclusão lógica com `deleted_at` quando não houver padrão existente de exclusão definitiva.
- Adicionar `deleted_by` se o projeto já possuir autenticação/usuários.
- Garantir que registros excluídos não apareçam em listagens, filtros ou sugestões.
- Validar impactos em arquivos associados, resumos, embeddings, logs e vínculos de rótulos.

**Critérios de aceite:**

- Excluir uma transcrição remove o item da listagem principal.
- O backend bloqueia ações em registros já excluídos.
- A exclusão não quebra vínculos, histórico ou telas que consultem dados agregados.

### F3.1.4 — Criar entidade de rótulos

**Descrição:** Criar cadastro de rótulos reutilizáveis para clientes, assuntos e outros agrupamentos.

**Campos sugeridos:**

- `id`
- `name`
- `slug`
- `description`
- `type` ou `category`, com valores como `client`, `subject`, `other`
- `color`, se o padrão visual atual permitir
- `is_active`
- `created_at`
- `updated_at`
- `deleted_at`, se o projeto usa soft delete

**Tarefas:**

- Criar migration da tabela/coleção de rótulos.
- Garantir unicidade de `slug` ou nome normalizado.
- Criar repository/data access para CRUD de rótulos.
- Criar validação de nome obrigatório e tamanho máximo.
- Criar normalização de nome para evitar duplicidade por diferença de caixa, acento ou espaços.

**Critérios de aceite:**

- É possível cadastrar, editar, listar, desativar/excluir e consultar rótulos.
- Não é possível criar rótulos duplicados semanticamente iguais.
- Rótulos inativos/excluídos não aparecem como opção padrão para novas atribuições.

### F3.1.5 — Criar relacionamento entre rótulos e reuniões/transcrições

**Descrição:** Permitir associar múltiplos rótulos a uma transcrição/reunião e reutilizar um rótulo em várias transcrições.

**Campos sugeridos para a tabela de vínculo:**

- `id`
- `meeting_id` ou `transcription_id`
- `label_id`
- `assigned_source`, com valores como `manual`, `suggestion`, `system`
- `confidence`, opcional para rótulos aceitos a partir de sugestão
- `assigned_by`, se houver usuário autenticado
- `created_at`

**Tarefas:**

- Criar migration da tabela/coleção de vínculo.
- Garantir unicidade do par reunião/transcrição + rótulo.
- Criar métodos para adicionar, remover e listar rótulos vinculados.
- Ajustar consultas de reunião/transcrição para retornar rótulos associados quando necessário.

**Critérios de aceite:**

- Uma reunião/transcrição pode ter múltiplos rótulos.
- O mesmo rótulo pode ser aplicado a múltiplas reuniões/transcrições.
- A API impede vínculo duplicado.

### F3.1.6 — Criar persistência para sugestões de rótulos

**Descrição:** Persistir sugestões geradas automaticamente para revisão do usuário.

**Campos sugeridos:**

- `id`
- `meeting_id` ou `transcription_id`
- `label_id`, quando a sugestão corresponder a um rótulo existente
- `suggested_name`, quando for sugestão de novo rótulo
- `confidence`
- `reason` ou `evidence`
- `status`, com valores como `pending`, `accepted`, `rejected`
- `created_at`
- `reviewed_at`
- `reviewed_by`, se houver usuário autenticado

**Tarefas:**

- Criar migration da tabela/coleção de sugestões.
- Criar repository/data access para salvar e consultar sugestões.
- Evitar sugestões duplicadas para a mesma transcrição.
- Permitir registrar aceite ou rejeição de sugestão.

**Critérios de aceite:**

- Sugestões são persistidas após processamento ou acionamento manual.
- Sugestões aceitas viram rótulos atribuídos.
- Sugestões rejeitadas não são reapresentadas como pendentes para a mesma transcrição.

---

## Épico F3.2 — Backend, serviços e regras de negócio

### F3.2.1 — Atualizar listagem de transcrições processadas

**Descrição:** Permitir listar transcrições processadas considerando status ativo, arquivado, excluído e filtros por rótulo.

**Tarefas:**

- Adicionar filtros de listagem para `processed`, `archived`, `active` e rótulos.
- Garantir paginação conforme padrão atual.
- Garantir ordenação por data da reunião/processamento conforme comportamento existente.
- Excluir registros com `deleted_at` da listagem padrão.

**Critérios de aceite:**

- A listagem principal mostra apenas transcrições processadas e não arquivadas.
- Existe filtro para consultar arquivadas.
- Existe filtro por um ou mais rótulos.

### F3.2.2 — Criar serviço de arquivamento em lote

**Descrição:** Implementar regra para arquivar uma ou mais transcrições processadas selecionadas.

**Tarefas:**

- Criar use case/service para arquivar transcrições.
- Validar que todos os IDs enviados existem.
- Validar que os itens estão processados.
- Ignorar ou retornar erro controlado para itens já arquivados.
- Registrar data de arquivamento.
- Retornar resumo da operação com sucesso, falhas e itens ignorados.

**Critérios de aceite:**

- Usuário consegue arquivar uma ou várias transcrições processadas.
- O backend não arquiva transcrições inexistentes, excluídas ou não processadas.
- A operação retorna resultado claro para a interface.

### F3.2.3 — Criar serviço de exclusão em lote

**Descrição:** Implementar regra para excluir uma ou mais transcrições processadas selecionadas.

**Tarefas:**

- Criar use case/service para exclusão segura.
- Validar que todos os IDs enviados existem.
- Validar que os itens estão processados.
- Aplicar soft delete ou exclusão conforme padrão atual.
- Remover ou invalidar sugestões pendentes relacionadas.
- Preservar consistência de vínculos de rótulos conforme padrão de exclusão adotado.
- Retornar resumo da operação com sucesso, falhas e itens ignorados.

**Critérios de aceite:**

- Usuário consegue excluir uma ou várias transcrições processadas.
- Registros excluídos não aparecem na listagem principal.
- A operação não remove acidentalmente itens não selecionados.

### F3.2.4 — Criar endpoints de ações em lote

**Descrição:** Expor APIs para arquivar e excluir transcrições processadas selecionadas.

**Endpoints sugeridos:**

- `POST /transcriptions/bulk/archive`
- `POST /transcriptions/bulk/delete`
- `POST /transcriptions/bulk/restore`, caso o produto permita restaurar arquivadas

**Tarefas:**

- Criar DTO/schema de entrada com lista de IDs.
- Validar limite máximo de itens por requisição.
- Validar permissões quando houver autenticação.
- Padronizar respostas de erro conforme o projeto.
- Adicionar testes de contrato/API.

**Critérios de aceite:**

- Endpoints seguem o padrão de rotas, autenticação e resposta do app.
- Requisições inválidas retornam mensagens claras.
- Operações em lote são idempotentes quando possível.

### F3.2.5 — Criar CRUD de rótulos

**Descrição:** Disponibilizar serviços e endpoints para gerenciar rótulos.

**Endpoints sugeridos:**

- `GET /labels`
- `POST /labels`
- `GET /labels/:id`
- `PATCH /labels/:id`
- `DELETE /labels/:id` ou `PATCH /labels/:id/deactivate`

**Tarefas:**

- Criar service/use case de criação de rótulo.
- Criar service/use case de edição de rótulo.
- Criar service/use case de listagem com busca por nome/tipo.
- Criar service/use case de desativação/exclusão.
- Impedir remoção destrutiva de rótulo usado em reuniões, salvo se o padrão atual permitir.

**Critérios de aceite:**

- Usuário consegue criar e editar rótulos.
- Usuário consegue listar rótulos disponíveis.
- Rótulos em uso são tratados com segurança na exclusão/desativação.

### F3.2.6 — Criar APIs para atribuição manual de rótulos

**Descrição:** Permitir adicionar e remover rótulos de uma reunião/transcrição.

**Endpoints sugeridos:**

- `GET /transcriptions/:id/labels`
- `POST /transcriptions/:id/labels`
- `DELETE /transcriptions/:id/labels/:labelId`

**Tarefas:**

- Criar validação para impedir atribuição a transcrição excluída.
- Criar validação para impedir atribuição de rótulo inexistente, inativo ou excluído.
- Garantir que adicionar o mesmo rótulo duas vezes não gere duplicidade.
- Retornar lista atualizada de rótulos após alteração.

**Critérios de aceite:**

- Usuário consegue atribuir rótulos existentes a uma transcrição.
- Usuário consegue remover rótulos de uma transcrição.
- A API mantém consistência em chamadas repetidas.

### F3.2.7 — Criar serviço de sugestão automática de rótulos

**Descrição:** Criar serviço responsável por sugerir rótulos com base no texto da transcrição.

**Tarefas:**

- Receber texto da transcrição, metadados da reunião e lista de rótulos ativos.
- Identificar rótulos existentes compatíveis com clientes, assuntos ou termos recorrentes.
- Calcular `confidence` para cada sugestão.
- Retornar evidência curta ou justificativa da sugestão.
- Definir limite mínimo de confiança para salvar sugestão.
- Evitar sugerir rótulos já atribuídos.
- Evitar sugerir rótulos já rejeitados para a mesma transcrição.

**Critérios de aceite:**

- O serviço sugere rótulos existentes relevantes para uma transcrição.
- Sugestões possuem confiança e justificativa.
- O serviço não aplica rótulos automaticamente sem aceite do usuário.

### F3.2.8 — Integrar sugestão de rótulos ao pipeline de transcrição

**Descrição:** Após a transcrição ser processada, gerar sugestões de rótulos automaticamente.

**Tarefas:**

- Localizar o ponto atual em que a transcrição passa para status processado.
- Acionar o serviço de sugestão após o processamento bem-sucedido.
- Garantir que falha na sugestão não quebre o processamento da transcrição.
- Registrar logs de erro e sucesso da sugestão.
- Evitar geração duplicada em reprocessamentos.

**Critérios de aceite:**

- Toda nova transcrição processada recebe tentativa de sugestão de rótulos.
- Erros de IA/classificação são tratados sem impactar a transcrição.
- Sugestões ficam disponíveis para revisão na interface.

### F3.2.9 — Criar endpoint para gerar sugestões sob demanda

**Descrição:** Permitir que o usuário gere ou atualize sugestões de rótulos manualmente.

**Endpoint sugerido:**

- `POST /transcriptions/:id/label-suggestions/generate`

**Tarefas:**

- Validar que a transcrição está processada.
- Validar que a transcrição não está excluída.
- Permitir regeneração apenas conforme regra definida para não duplicar sugestões.
- Retornar lista de sugestões atualizada.

**Critérios de aceite:**

- Usuário consegue solicitar sugestões para uma transcrição processada.
- Sugestões repetidas não são duplicadas.
- A API retorna erro controlado quando a transcrição não está apta.

### F3.2.10 — Criar endpoints para aceitar e rejeitar sugestões

**Descrição:** Permitir revisão das sugestões automáticas pelo usuário.

**Endpoints sugeridos:**

- `GET /transcriptions/:id/label-suggestions`
- `POST /transcriptions/:id/label-suggestions/:suggestionId/accept`
- `POST /transcriptions/:id/label-suggestions/:suggestionId/reject`

**Tarefas:**

- Listar sugestões pendentes, aceitas e rejeitadas conforme necessidade da tela.
- Ao aceitar, criar vínculo definitivo entre rótulo e transcrição.
- Ao rejeitar, atualizar status da sugestão.
- Se a sugestão for de novo rótulo, permitir criação controlada antes de atribuir.

**Critérios de aceite:**

- Sugestões pendentes aparecem para revisão.
- Sugestão aceita vira rótulo aplicado.
- Sugestão rejeitada deixa de aparecer como pendente.

---

## Épico F3.3 — Interface de usuário

### F3.3.1 — Adicionar seleção múltipla na listagem de transcrições processadas

**Descrição:** Permitir selecionar uma ou mais transcrições processadas na listagem.

**Tarefas:**

- Adicionar checkbox por item ou modo de seleção conforme padrão visual do aplicativo.
- Adicionar opção de selecionar todos os itens visíveis na página atual.
- Manter seleção ao navegar/filtro somente se o padrão atual permitir.
- Desabilitar seleção para itens não processados, quando apareçam na tela.

**Critérios de aceite:**

- Usuário consegue selecionar uma transcrição.
- Usuário consegue selecionar múltiplas transcrições.
- A interface mostra claramente a quantidade de itens selecionados.

### F3.3.2 — Criar barra de ações em lote

**Descrição:** Exibir ações disponíveis quando houver transcrições selecionadas.

**Tarefas:**

- Criar barra ou menu de ações com “Arquivar” e “Excluir”.
- Mostrar quantidade de itens selecionados.
- Desabilitar ações durante carregamento.
- Limpar seleção após operação concluída.

**Critérios de aceite:**

- Ações em lote aparecem apenas quando há seleção.
- Usuário sabe quantos itens serão afetados.
- A interface atualiza a listagem após ação concluída.

### F3.3.3 — Criar confirmação para arquivamento

**Descrição:** Evitar arquivamento acidental de transcrições selecionadas.

**Tarefas:**

- Criar modal/diálogo de confirmação.
- Informar quantidade de itens selecionados.
- Explicar que arquivar remove da listagem padrão, mas mantém os dados.
- Exibir feedback de sucesso ou erro.

**Critérios de aceite:**

- Arquivamento só ocorre após confirmação.
- Usuário recebe feedback do resultado da operação.

### F3.3.4 — Criar confirmação para exclusão

**Descrição:** Evitar exclusão acidental de transcrições selecionadas.

**Tarefas:**

- Criar modal/diálogo de confirmação com linguagem mais restritiva que arquivamento.
- Informar quantidade de itens selecionados.
- Explicar se a exclusão é lógica ou definitiva conforme implementação adotada.
- Exibir feedback de sucesso ou erro.

**Critérios de aceite:**

- Exclusão só ocorre após confirmação explícita.
- Usuário entende o impacto da exclusão antes de confirmar.

### F3.3.5 — Adicionar filtro/visão de arquivadas

**Descrição:** Permitir consultar transcrições arquivadas.

**Tarefas:**

- Adicionar filtro de status com opção “Ativas” e “Arquivadas”.
- Ajustar chamada da API para enviar o filtro correto.
- Diferenciar visualmente itens arquivados quando exibidos.
- Se houver restauração, exibir ação para restaurar arquivadas.

**Critérios de aceite:**

- Usuário consegue visualizar transcrições arquivadas.
- Transcrições arquivadas não aparecem misturadas na listagem padrão.

### F3.3.6 — Criar tela ou modal de cadastro de rótulos

**Descrição:** Permitir administrar rótulos de clientes, assuntos e outros agrupamentos.

**Tarefas:**

- Criar formulário de criação de rótulo.
- Criar edição de rótulo.
- Criar listagem de rótulos existentes.
- Adicionar busca por nome.
- Adicionar filtro por tipo/categoria, se implementado.
- Exibir estado vazio quando não houver rótulos.

**Critérios de aceite:**

- Usuário consegue cadastrar rótulos.
- Usuário consegue editar rótulos.
- Usuário consegue localizar rótulos existentes.

### F3.3.7 — Criar seletor de rótulos na reunião/transcrição

**Descrição:** Permitir aplicar e remover rótulos manualmente em uma reunião/transcrição.

**Tarefas:**

- Exibir rótulos já aplicados.
- Criar seletor com busca por rótulo existente.
- Permitir remover rótulo aplicado.
- Permitir criar novo rótulo durante atribuição apenas se o padrão de UX do app permitir.
- Atualizar interface sem recarregar toda a página quando possível.

**Critérios de aceite:**

- Usuário consegue ver rótulos aplicados à transcrição.
- Usuário consegue aplicar rótulos existentes.
- Usuário consegue remover rótulos aplicados.

### F3.3.8 — Exibir sugestões automáticas de rótulos

**Descrição:** Mostrar na interface os rótulos sugeridos pelo sistema para revisão.

**Tarefas:**

- Exibir sugestões pendentes na tela de detalhe da transcrição ou card da reunião.
- Mostrar nome do rótulo sugerido, confiança e justificativa curta.
- Criar ações “Aceitar” e “Rejeitar”.
- Atualizar lista de rótulos aplicados ao aceitar sugestão.
- Remover sugestão pendente ao rejeitar.

**Critérios de aceite:**

- Usuário vê sugestões automáticas quando existirem.
- Usuário consegue aceitar uma sugestão.
- Usuário consegue rejeitar uma sugestão.

### F3.3.9 — Adicionar ação para gerar sugestões manualmente

**Descrição:** Permitir que o usuário solicite sugestões quando não houver sugestões ou quando desejar recalcular.

**Tarefas:**

- Criar botão “Sugerir rótulos” ou equivalente.
- Mostrar estado de carregamento.
- Exibir mensagem quando nenhuma sugestão for encontrada.
- Tratar erros do serviço de sugestão.

**Critérios de aceite:**

- Usuário consegue disparar sugestão manualmente em transcrição processada.
- A interface mostra resultado ou ausência de sugestões.

### F3.3.10 — Adicionar filtro por rótulos na listagem

**Descrição:** Permitir filtrar transcrições/reuniões por rótulo aplicado.

**Tarefas:**

- Adicionar seletor de rótulo na listagem.
- Permitir filtrar por um ou mais rótulos, conforme padrão de filtros do app.
- Atualizar query da API.
- Exibir rótulos nos cards/linhas da listagem.

**Critérios de aceite:**

- Usuário consegue filtrar transcrições por rótulo.
- Resultado da listagem corresponde aos rótulos selecionados.

---

## Épico F3.4 — IA, classificação e qualidade das sugestões

### F3.4.1 — Definir estratégia inicial de sugestão

**Descrição:** Definir se a sugestão usará correspondência determinística, modelo de IA, embeddings ou combinação de métodos.

**Tarefas:**

- Avaliar serviços de IA já existentes no projeto.
- Reutilizar cliente/pipeline de IA atual quando existir.
- Criar fallback por correspondência de palavras-chave com nomes e aliases de rótulos.
- Definir regra de confiança mínima.
- Definir limite máximo de sugestões por transcrição.

**Critérios de aceite:**

- A estratégia reutiliza infraestrutura existente de IA quando disponível.
- Há fallback simples para evitar dependência total do modelo.
- As sugestões são limitadas e ordenadas por relevância.

### F3.4.2 — Criar normalização de texto para sugestão

**Descrição:** Preparar a transcrição para classificação sem alterar o texto original armazenado.

**Tarefas:**

- Remover excesso de espaços e quebras irrelevantes.
- Normalizar caixa, acentos e pontuação para matching.
- Limitar tamanho do texto enviado ao serviço de IA conforme padrão/custo.
- Preservar trechos de evidência para justificar sugestões.

**Critérios de aceite:**

- Normalização não altera o conteúdo original da transcrição.
- O serviço consegue processar transcrições longas de forma controlada.

### F3.4.3 — Criar cálculo de confiança e justificativa

**Descrição:** Padronizar o retorno das sugestões.

**Tarefas:**

- Definir escala de confiança de 0 a 1 ou 0 a 100 conforme padrão do app.
- Criar justificativa curta baseada em termos ou contexto da transcrição.
- Evitar expor trechos longos demais da transcrição.
- Ordenar sugestões por confiança.

**Critérios de aceite:**

- Cada sugestão possui score de confiança.
- Cada sugestão possui justificativa curta.
- Sugestões abaixo do limite mínimo não são exibidas por padrão.

### F3.4.4 — Evitar sugestões indevidas ou duplicadas

**Descrição:** Reduzir ruído das sugestões automáticas.

**Tarefas:**

- Não sugerir rótulo já atribuído.
- Não sugerir rótulo rejeitado para a mesma transcrição.
- Agrupar sugestões semanticamente equivalentes.
- Aplicar limite máximo de sugestões exibidas.

**Critérios de aceite:**

- A interface não mostra sugestões repetidas.
- Usuário não recebe novamente uma sugestão rejeitada para a mesma transcrição.

---

## Épico F3.5 — Permissões, auditoria e segurança

### F3.5.1 — Aplicar permissões nas novas ações

**Descrição:** Garantir que apenas usuários autorizados executem ações sensíveis.

**Tarefas:**

- Reutilizar middleware/guard atual de autenticação e autorização.
- Definir permissão para arquivar transcrições.
- Definir permissão para excluir transcrições.
- Definir permissão para gerenciar rótulos.
- Definir permissão para aceitar/rejeitar sugestões, se aplicável.

**Critérios de aceite:**

- Usuário sem permissão não consegue arquivar, excluir ou gerenciar rótulos.
- APIs retornam erro padronizado de autorização.

### F3.5.2 — Registrar auditoria das ações críticas

**Descrição:** Registrar eventos importantes para rastreabilidade.

**Tarefas:**

- Registrar quem arquivou uma transcrição e quando.
- Registrar quem excluiu uma transcrição e quando.
- Registrar criação, edição e desativação de rótulos.
- Registrar aceite e rejeição de sugestões.
- Usar mecanismo de log/auditoria já existente no app quando houver.

**Critérios de aceite:**

- Ações críticas ficam rastreáveis.
- Logs não expõem dados sensíveis desnecessários da transcrição.

---

## Épico F3.6 — Testes e validação

### F3.6.1 — Testes unitários de serviços

**Tarefas:**

- Testar arquivamento em lote.
- Testar exclusão em lote.
- Testar criação e edição de rótulos.
- Testar atribuição e remoção de rótulos.
- Testar geração de sugestões com rótulos existentes.
- Testar bloqueio de duplicidade de rótulos e sugestões.

**Critérios de aceite:**

- Regras de negócio principais cobertas por testes unitários.

### F3.6.2 — Testes de integração/API

**Tarefas:**

- Testar endpoints de arquivamento e exclusão em lote.
- Testar endpoints de CRUD de rótulos.
- Testar endpoints de vínculo de rótulos.
- Testar endpoints de sugestão, aceite e rejeição.
- Testar filtros por status e rótulo.

**Critérios de aceite:**

- APIs retornam status codes e payloads padronizados.
- Fluxos principais funcionam com banco real/de teste.

### F3.6.3 — Testes de interface/E2E

**Tarefas:**

- Selecionar múltiplas transcrições e arquivar.
- Selecionar múltiplas transcrições e excluir.
- Criar rótulo e aplicar a uma transcrição.
- Filtrar transcrições por rótulo.
- Visualizar, aceitar e rejeitar sugestão automática.
- Consultar transcrições arquivadas.

**Critérios de aceite:**

- Fluxos principais funcionam de ponta a ponta.
- Estados de carregamento, erro e sucesso são exibidos corretamente.

### F3.6.4 — Testes de regressão

**Tarefas:**

- Garantir que o processamento de novas transcrições continua funcionando.
- Garantir que listagens existentes não exibem arquivadas/excluídas indevidamente.
- Garantir que dashboards/contadores não sejam quebrados por novos status.
- Garantir que exports, resumos ou buscas existentes respeitam arquivamento/exclusão conforme regra definida.

**Critérios de aceite:**

- Funcionalidades existentes permanecem estáveis após a fase 3.

---

## Épico F3.7 — Documentação e entrega

### F3.7.1 — Atualizar documentação técnica

**Tarefas:**

- Documentar novas tabelas/coleções e relacionamentos.
- Documentar endpoints adicionados.
- Documentar regras de arquivamento, exclusão e rótulos.
- Documentar fluxo de sugestão automática.
- Documentar variáveis de ambiente novas, se houver uso de IA/modelos.

**Critérios de aceite:**

- Desenvolvedores conseguem entender e manter as funcionalidades da fase 3.

### F3.7.2 — Criar checklist de release da fase 3

**Tarefas:**

- Validar execução das migrations.
- Validar permissões em ambiente de staging.
- Validar geração de sugestões em transcrições reais de teste.
- Validar filtros e ações em lote com volume representativo.
- Validar logs de erro e auditoria.

**Critérios de aceite:**

- Fase 3 pronta para homologação com os fluxos principais validados.

---

## Ordem sugerida de implementação

1. F3.1.1 — Mapear entidades atuais de reunião/transcrição.
2. F3.1.2 — Criar suporte de arquivamento.
3. F3.1.3 — Criar suporte de exclusão segura.
4. F3.1.4 — Criar entidade de rótulos.
5. F3.1.5 — Criar relacionamento entre rótulos e reuniões/transcrições.
6. F3.1.6 — Criar persistência para sugestões de rótulos.
7. F3.2.1 — Atualizar listagem de transcrições processadas.
8. F3.2.2 — Criar serviço de arquivamento em lote.
9. F3.2.3 — Criar serviço de exclusão em lote.
10. F3.2.4 — Criar endpoints de ações em lote.
11. F3.2.5 — Criar CRUD de rótulos.
12. F3.2.6 — Criar APIs para atribuição manual de rótulos.
13. F3.4.1 — Definir estratégia inicial de sugestão.
14. F3.4.2 — Criar normalização de texto para sugestão.
15. F3.4.3 — Criar cálculo de confiança e justificativa.
16. F3.4.4 — Evitar sugestões indevidas ou duplicadas.
17. F3.2.7 — Criar serviço de sugestão automática de rótulos.
18. F3.2.8 — Integrar sugestão de rótulos ao pipeline de transcrição.
19. F3.2.9 — Criar endpoint para gerar sugestões sob demanda.
20. F3.2.10 — Criar endpoints para aceitar e rejeitar sugestões.
21. F3.3.1 — Adicionar seleção múltipla na listagem.
22. F3.3.2 — Criar barra de ações em lote.
23. F3.3.3 — Criar confirmação para arquivamento.
24. F3.3.4 — Criar confirmação para exclusão.
25. F3.3.5 — Adicionar filtro/visão de arquivadas.
26. F3.3.6 — Criar tela ou modal de cadastro de rótulos.
27. F3.3.7 — Criar seletor de rótulos na reunião/transcrição.
28. F3.3.8 — Exibir sugestões automáticas de rótulos.
29. F3.3.9 — Adicionar ação para gerar sugestões manualmente.
30. F3.3.10 — Adicionar filtro por rótulos na listagem.
31. F3.5.1 — Aplicar permissões nas novas ações.
32. F3.5.2 — Registrar auditoria das ações críticas.
33. F3.6.1 — Testes unitários de serviços.
34. F3.6.2 — Testes de integração/API.
35. F3.6.3 — Testes de interface/E2E.
36. F3.6.4 — Testes de regressão.
37. F3.7.1 — Atualizar documentação técnica.
38. F3.7.2 — Criar checklist de release da fase 3.

## Critérios gerais de aceite da fase 3

- Usuário consegue selecionar transcrições processadas e executar arquivamento em lote.
- Usuário consegue selecionar transcrições processadas e executar exclusão em lote com confirmação.
- Transcrições arquivadas deixam de aparecer na listagem padrão e podem ser consultadas por filtro.
- Transcrições excluídas deixam de aparecer nas listagens e não recebem novas ações.
- Usuário consegue cadastrar, editar, listar e desativar/excluir rótulos.
- Usuário consegue atribuir e remover rótulos manualmente em reuniões/transcrições.
- O sistema sugere rótulos com base no conteúdo da transcrição.
- Usuário consegue aceitar ou rejeitar sugestões de rótulos.
- Usuário consegue filtrar transcrições por rótulos.
- Funcionalidades existentes de processamento de transcrição permanecem funcionando.
