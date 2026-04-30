# Fase 4 — Memória de stakeholders, rótulos inteligentes, oportunidades, riscos, pendências e indicadores por cliente

## 1. Objetivo

Evoluir a ferramenta para apoiar o dia a dia de uma consultoria, transformando reuniões processadas localmente em uma base operacional de relacionamento, oportunidades, riscos, pendências e indicadores por cliente.

Esta fase complementa a evolução de identificação de participantes, falas e memória local de voz, adicionando recursos voltados para gestão de clientes, acompanhamento de projetos, identificação de oportunidades comerciais, controle de riscos e leitura objetiva do volume de reuniões por cliente.

A ferramenta deve continuar seguindo a premissa **local-first**:

- as funcionalidades internas devem operar localmente;
- a aplicação não deve depender de Teams, Microsoft 365, Google, Zoom, CRM, ferramentas de gestão ou qualquer serviço externo para funcionar;
- conectores externos podem existir como entradas opcionais ou canais auxiliares;
- todo processamento principal deve poder ser feito a partir de arquivos locais, transcrições locais, banco local, modelos locais e configurações locais.

Em outras palavras: integrações como Teams são permitidas, mas o núcleo do produto deve permanecer independente.

---

## 2. Escopo desta documentação

Esta documentação detalha os seguintes módulos da Fase 4:

1. **Memória local de pessoas e stakeholders**
2. **Sugestão de rótulos por pessoa, cliente e assunto**
3. **Detector de oportunidades comerciais**
4. **Detector de riscos e mudanças de escopo**
5. **Central de pendências por cliente**
6. **Indicadores por cliente e tempo de reunião**

Os módulos devem funcionar de forma integrada. A memória de pessoas deve melhorar as sugestões de rótulos. Os rótulos devem melhorar a identificação de oportunidades e riscos. As pendências devem ser associadas a clientes e pessoas. Os indicadores devem consolidar volume de reunião, recorrência, comportamento histórico e desvios em relação ao padrão de cada cliente.

---

## 3. Premissas de arquitetura

### 3.1. Núcleo local obrigatório

O núcleo da ferramenta deve conter localmente:

- cadastro de reuniões;
- transcrições processadas;
- participantes identificados;
- memória local de pessoas;
- memória local de voz, quando habilitada;
- rótulos;
- clientes;
- assuntos recorrentes;
- oportunidades;
- riscos;
- mudanças de escopo;
- pendências;
- indicadores;
- histórico de auditoria;
- base de busca local;
- modelos locais necessários para sugestão, classificação e extração.

A indisponibilidade de conexão externa não deve impedir:

- abrir reuniões já processadas;
- processar arquivos locais;
- consultar histórico;
- gerar sugestões a partir de transcrições locais;
- revisar sugestões;
- alterar rótulos;
- consultar indicadores;
- exportar relatórios;
- usar a central de pendências.

### 3.2. Conectores externos como adaptadores opcionais

Integrações com Teams, Outlook, SharePoint, CRM, Jira, Planner ou outras plataformas podem existir, mas devem ser tratadas como **adaptadores opcionais**.

Esses adaptadores podem:

- importar gravações;
- importar transcrições;
- importar metadados de reunião;
- importar lista de participantes;
- importar título, data e duração;
- publicar resumos ou follow-ups, quando configurado;
- criar links de referência para reunião externa;
- facilitar o preenchimento de dados.

Esses adaptadores não devem ser necessários para:

- transcrever;
- diarizar;
- identificar pessoas recorrentes;
- sugerir rótulos;
- detectar oportunidades;
- detectar riscos;
- detectar mudanças de escopo;
- calcular indicadores;
- consultar pendências;
- gerar relatórios.

### 3.3. Decisões orientadas por evidência

Toda sugestão automática deve ter evidência rastreável.

Exemplos:

- trecho da transcrição;
- timestamp;
- reunião de origem;
- participante provável;
- rótulos usados na inferência;
- regra ou modelo que gerou a sugestão;
- nível de confiança.

O usuário deve conseguir entender por que a ferramenta sugeriu uma pessoa, rótulo, oportunidade, risco, mudança de escopo ou pendência.

### 3.4. Humano no controle

A ferramenta deve sugerir, mas o usuário deve revisar.

Ações automáticas sensíveis devem ser configuráveis e, por padrão, passar por confirmação humana:

- confirmar identidade de pessoa por voz;
- aplicar rótulo novo;
- criar oportunidade comercial;
- registrar risco;
- registrar mudança de escopo;
- atribuir pendência a uma pessoa;
- indicar que um cliente está abaixo ou acima do padrão de reunião;
- publicar algo em plataforma externa.

### 3.5. Aprendizado local por feedback

O comportamento da ferramenta deve melhorar com o uso, sem depender de serviços externos.

Exemplos de feedback local:

- rótulo aceito;
- rótulo rejeitado;
- pessoa corrigida;
- oportunidade confirmada;
- risco descartado;
- mudança de escopo validada;
- pendência marcada como incorreta;
- cliente associado manualmente à reunião.

Esses eventos devem alimentar regras e modelos locais para reduzir falsos positivos e melhorar sugestões futuras.

---

## 4. Visão geral dos módulos

```text
Core local da Fase 4
├── Memória local de pessoas e stakeholders
├── Sugestão de rótulos por pessoa, cliente e assunto
├── Detector de oportunidades comerciais
├── Detector de riscos e mudanças de escopo
├── Central de pendências por cliente
├── Indicadores por cliente e tempo de reunião
├── Auditoria e histórico de revisão
├── Exportações locais
└── Conectores opcionais
    ├── Teams
    ├── Outlook/Calendário
    ├── Upload manual
    ├── Pasta local monitorada
    └── Importação de arquivos
```

Fluxo recomendado após uma reunião:

1. A reunião entra na ferramenta por upload manual, captura local, pasta monitorada ou conector opcional.
2. A ferramenta normaliza os metadados.
3. O áudio, vídeo ou transcrição é processado localmente.
4. O sistema identifica falantes e possíveis pessoas recorrentes.
5. O sistema sugere cliente, pessoas, rótulos e assuntos.
6. O sistema extrai pendências, decisões, riscos, mudanças de escopo e oportunidades.
7. O usuário revisa as sugestões.
8. Os dados confirmados alimentam a memória local.
9. Os indicadores do cliente são recalculados.
10. A reunião fica disponível na central do cliente e na busca local.

---

# 5. Memória local de pessoas e stakeholders

## 5.1. Objetivo

Criar uma memória local de pessoas recorrentes nas reuniões, permitindo que a ferramenta reconheça participantes ao longo do tempo, associe essas pessoas a clientes, projetos, rótulos, papéis e histórico de interação.

A memória deve ajudar a responder perguntas como:

- Quem costuma participar das reuniões deste cliente?
- Quem é o ponto focal?
- Quem parece aprovar decisões?
- Quem costuma falar sobre temas técnicos?
- Quem está associado a pendências em aberto?
- Quem participou de reuniões sobre determinado assunto?
- Qual pessoa recorrente foi detectada pela voz, mas ainda não está identificada?

## 5.2. Conceitos principais

### Pessoa

Representa um indivíduo identificado ou recorrente na base local.

Exemplos:

- Ana Souza;
- Roberto Lima;
- Participante não identificado 03;
- Voz recorrente A;
- Consultor interno 01.

### Stakeholder

Pessoa associada a um cliente, projeto ou contexto de relacionamento.

A mesma pessoa pode ser stakeholder em mais de um cliente ou projeto.

Exemplo:

- Roberto Lima como `TI` no Cliente XPTO;
- Roberto Lima como `Aprovador técnico` no Projeto CRM;
- Ana Souza como `Patrocinadora` no Cliente XPTO.

### Participante de reunião

Ocorrência de uma pessoa em uma reunião específica.

Pode começar como genérico:

- Speaker 1;
- Speaker 2;
- Participante do Teams;
- Usuário informado manualmente;
- Voz provável de Ana Souza.

Depois pode ser confirmado como uma pessoa real.

### Memória de voz

Assinatura local de voz usada para sugerir que um falante recorrente pode ser a mesma pessoa em diferentes reuniões.

A memória de voz deve ser local, revisável e removível.

### Evidência de relacionamento

Conjunto de dados que sustenta a associação de uma pessoa a um cliente, papel ou rótulo.

Exemplos:

- participou de 7 reuniões do Cliente XPTO;
- foi citada como responsável por validação;
- aparece em falas sobre ambiente, segurança e acesso;
- foi confirmada manualmente como ponto focal;
- teve voz reconhecida em reuniões anteriores.

## 5.3. Requisitos funcionais

### F4-PES-001 — Cadastro local de pessoas

A ferramenta deve permitir cadastrar pessoas localmente.

Campos sugeridos:

- nome;
- apelido;
- e-mail opcional;
- telefone opcional;
- empresa;
- cliente principal;
- área;
- cargo ou papel informado;
- tipo: `interno`, `cliente`, `parceiro`, `fornecedor`, `desconhecido`;
- rótulos associados;
- observações;
- status: `ativo`, `inativo`, `mesclado`, `desconhecido`;
- data de criação;
- data da última aparição em reunião.

### F4-PES-002 — Criação automática de pessoas temporárias

Quando o sistema detectar um falante novo, deve criar uma entidade temporária.

Exemplos:

- `Pessoa não identificada 01`;
- `Voz recorrente 03`;
- `Participante externo sem nome`.

Essa pessoa temporária pode depois ser:

- confirmada como uma pessoa nova;
- vinculada a uma pessoa existente;
- ignorada;
- mesclada com outro registro;
- excluída da memória.

### F4-PES-003 — Identificação de recorrência

A ferramenta deve identificar quando uma pessoa ou voz aparece em múltiplas reuniões.

Critérios possíveis:

- mesmo e-mail importado de metadados;
- mesmo nome de participante;
- mesma assinatura de voz local;
- mesmo padrão de participação;
- mesma associação recorrente com cliente;
- confirmação manual anterior;
- rótulos e assuntos semelhantes.

A ferramenta deve exibir a recorrência com evidência.

Exemplo:

> Esta voz aparece em 5 reuniões do Cliente XPTO e foi confirmada como Ana Souza em 3 delas.

### F4-PES-004 — Perfil local da pessoa

Cada pessoa deve ter uma tela de perfil.

A tela deve exibir:

- dados cadastrais;
- clientes relacionados;
- projetos relacionados;
- rótulos associados;
- reuniões em que participou;
- tempo total em reunião;
- últimas aparições;
- principais assuntos discutidos;
- pendências atribuídas;
- decisões em que participou;
- riscos relacionados;
- oportunidades relacionadas;
- evidências de papel ou influência;
- histórico de correções.

### F4-PES-005 — Mapa de stakeholders por cliente

Para cada cliente, a ferramenta deve exibir um mapa de pessoas envolvidas.

Campos por stakeholder:

- nome;
- empresa;
- papel sugerido;
- papel confirmado;
- rótulos;
- frequência de participação;
- última reunião;
- assuntos recorrentes;
- pendências abertas;
- oportunidades associadas;
- riscos associados;
- nível de evidência;
- status de revisão.

Papéis sugeridos:

- patrocinador;
- decisor;
- influenciador;
- ponto focal;
- aprovador;
- usuário-chave;
- técnico;
- segurança da informação;
- jurídico;
- financeiro;
- operação;
- TI;
- negócio;
- consultor interno;
- gerente de projeto;
- responsável por homologação.

### F4-PES-006 — Mesclagem de pessoas duplicadas

A ferramenta deve permitir mesclar registros duplicados.

Exemplo:

- `Ana Souza`;
- `Ana S.`;
- `ana.souza@cliente.com`;
- `Voz recorrente 02`.

Ao mesclar, a ferramenta deve preservar:

- histórico de reuniões;
- rótulos;
- pendências;
- decisões;
- oportunidades;
- riscos;
- memória de voz, quando aplicável;
- auditoria da operação.

### F4-PES-007 — Separação de pessoas incorretamente unificadas

A ferramenta deve permitir desfazer ou corrigir uma associação indevida.

Exemplo:

O sistema sugeriu que `Speaker 2` era Roberto, mas o usuário corrigiu para Camila.

A correção deve:

- atualizar a reunião atual;
- registrar feedback negativo;
- reduzir a confiança dessa associação no futuro;
- preservar a evidência original para auditoria;
- permitir reprocessamento, quando necessário.

### F4-PES-008 — Associação de pessoa a cliente e projeto

O usuário deve poder associar uma pessoa a:

- cliente;
- projeto;
- unidade de negócio;
- área interna;
- tipo de relacionamento;
- período de vigência.

Uma pessoa pode ter mais de uma associação.

Exemplo:

```text
Pessoa: Ana Souza
Cliente: XPTO
Projeto: Implantação CRM
Papel: Patrocinadora
Vigência: 2026-02-01 até atual
Rótulos: decisor, executivo, negócio
```

### F4-PES-009 — Sugestão de rótulos para pessoas recorrentes

Com base nas reuniões, o sistema deve sugerir rótulos para pessoas.

Exemplos:

- `decisor`;
- `ponto focal`;
- `técnico`;
- `negócio`;
- `financeiro`;
- `segurança da informação`;
- `homologador`;
- `usuário-chave`;
- `consultor interno`;
- `aprovador`.

A sugestão deve considerar:

- frequência em reuniões;
- temas das falas;
- pendências atribuídas;
- decisões citadas;
- cargo informado;
- rótulos já usados em pessoas semelhantes;
- cliente associado;
- confirmação manual anterior.

### F4-PES-010 — Histórico de relacionamento da pessoa

A ferramenta deve manter uma linha do tempo local por pessoa.

Eventos possíveis:

- primeira reunião detectada;
- identidade confirmada;
- rótulo aplicado;
- pendência atribuída;
- decisão relacionada;
- oportunidade associada;
- risco mencionado;
- mudança de papel;
- correção manual;
- inativação.

## 5.4. Regras de negócio

1. Nenhuma identidade sugerida por voz deve ser tratada como definitiva sem confirmação, salvo se o usuário habilitar autoaplicação por confiança alta.
2. Toda identificação automática deve exibir confiança e evidência.
3. Pessoas temporárias devem ser visíveis em fila de revisão.
4. A exclusão de uma pessoa não deve apagar reuniões já processadas sem confirmação explícita.
5. Ao arquivar reunião, a participação histórica pode continuar sendo considerada em indicadores, salvo configuração contrária.
6. Ao excluir reunião, seus dados devem sair dos cálculos e da memória derivada, respeitando as regras de exclusão da aplicação.
7. A memória de pessoa deve ser editável e exportável localmente.
8. A pessoa deve poder solicitar remoção da memória local, caso o processo interno exija.

## 5.5. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `person` | Cadastro local de pessoas | id, name, email, company, type, status, notes |
| `person_alias` | Nomes alternativos | person_id, alias, source, confidence |
| `client_stakeholder` | Associação pessoa-cliente | person_id, client_id, role, status, evidence_score |
| `meeting_participant` | Participação em reunião | meeting_id, person_id, speaker_id, confidence, source |
| `voice_profile` | Memória local de voz | person_id, embedding_ref, status, created_at |
| `person_label` | Rótulos da pessoa | person_id, label_id, source, confidence |
| `person_timeline_event` | Linha do tempo | person_id, event_type, date, source_ref |
| `identity_suggestion` | Sugestões de identidade | meeting_id, speaker_id, suggested_person_id, confidence, status |

## 5.6. Telas sugeridas

### Tela: Pessoas

Deve permitir:

- listar pessoas;
- buscar por nome, cliente, rótulo ou assunto;
- filtrar por tipo;
- ver pessoas não identificadas;
- ver pessoas com sugestão pendente;
- mesclar duplicados;
- abrir perfil da pessoa.

### Tela: Perfil da pessoa

Deve mostrar:

- cadastro;
- rótulos;
- clientes;
- reuniões;
- tempo em reunião;
- pendências;
- riscos;
- oportunidades;
- decisões;
- histórico de identificação;
- evidências de papel.

### Tela: Stakeholders do cliente

Deve mostrar:

- mapa de pessoas do cliente;
- papéis sugeridos;
- influência operacional;
- última participação;
- assuntos recorrentes;
- pendências por pessoa;
- oportunidades relacionadas.

---

# 6. Sugestão de rótulos por pessoa, cliente e assunto

## 6.1. Objetivo

Expandir a funcionalidade de rótulos da Fase 3 para torná-la mais inteligente e contextual.

A ferramenta deve sugerir rótulos automaticamente para:

- reunião;
- transcrição;
- pessoa;
- cliente;
- pendência;
- risco;
- oportunidade;
- mudança de escopo;
- assunto recorrente.

## 6.2. Tipos de rótulos

Os rótulos devem ser organizados por tipo para reduzir ambiguidade.

Tipos sugeridos:

| Tipo de rótulo | Exemplo | Aplicação |
|---|---|---|
| Cliente | XPTO, ACME | Reunião, pessoa, pendência, oportunidade |
| Projeto | CRM 2026, CoE Power Platform | Reunião, risco, escopo, pendência |
| Pessoa/Papel | decisor, técnico, ponto focal | Pessoa, stakeholder |
| Assunto | governança, integração, dados | Reunião, trecho, pendência |
| Tecnologia | Power BI, Power Apps, Dynamics, SharePoint | Oportunidade, reunião, assunto |
| Comercial | oportunidade, proposta, expansão | Oportunidade, reunião |
| Risco | prazo, acesso, escopo, orçamento | Risco, reunião |
| Operacional | interno, status report, follow-up | Reunião, pendência |
| Confidencialidade | sensível, jurídico, financeiro | Reunião, trecho, exportação |

## 6.3. Fontes de sugestão

A ferramenta deve sugerir rótulos combinando múltiplas fontes locais:

- título da reunião;
- descrição;
- metadados importados;
- participantes;
- pessoas recorrentes;
- cliente associado;
- conteúdo da transcrição;
- termos frequentes;
- histórico de rótulos aceitos;
- rótulos associados a pessoas presentes;
- rótulos de reuniões anteriores semelhantes;
- oportunidades e riscos detectados;
- templates de reunião;
- memória local de voz, quando habilitada.

## 6.4. Requisitos funcionais

### F4-ROT-001 — Sugestão de rótulo para reunião

Após processar uma reunião, a ferramenta deve sugerir rótulos relevantes.

Exemplo:

```text
Reunião: Status semanal XPTO
Sugestões:
- Cliente: XPTO — confiança 94%
- Assunto: governança — confiança 82%
- Tecnologia: Power Platform — confiança 78%
- Tipo: status report — confiança 75%
```

### F4-ROT-002 — Sugestão de rótulo para pessoa

A ferramenta deve sugerir rótulos para pessoas com base em comportamento recorrente.

Exemplo:

```text
Pessoa: Roberto Lima
Sugestões:
- técnico — confiança 88%
- segurança da informação — confiança 74%
- aprovador técnico — confiança 68%
```

### F4-ROT-003 — Sugestão de rótulo para cliente

A ferramenta deve sugerir rótulos para clientes conforme padrões detectados.

Exemplo:

```text
Cliente: XPTO
Sugestões:
- alto volume de reuniões
- risco de escopo
- oportunidade de automação
- governança Power Platform
```

### F4-ROT-004 — Sugestão de rótulo por assunto recorrente

O sistema deve identificar assuntos recorrentes entre reuniões.

Exemplos:

- integração com ERP;
- aprovação de acesso;
- governança de ambiente;
- licenciamento;
- dashboard executivo;
- treinamento de usuários;
- homologação;
- migração de dados.

### F4-ROT-005 — Fila de revisão de rótulos

A ferramenta deve ter uma fila para revisar sugestões.

A fila deve permitir:

- aceitar rótulo;
- rejeitar rótulo;
- editar rótulo sugerido;
- criar novo rótulo;
- aplicar rótulo em lote;
- ocultar sugestões semelhantes;
- ver evidência da sugestão;
- filtrar por cliente, reunião, pessoa ou confiança.

### F4-ROT-006 — Aprendizado por feedback

Quando o usuário aceitar ou rejeitar um rótulo, a ferramenta deve registrar feedback.

Esse feedback deve influenciar:

- sugestões futuras para o mesmo cliente;
- sugestões futuras para a mesma pessoa;
- sugestões futuras para reuniões semelhantes;
- priorização de rótulos;
- bloqueio de rótulos rejeitados repetidamente.

## 6.5. Regras de negócio

1. A ferramenta não deve criar rótulos novos automaticamente sem configuração explícita.
2. Sugestões devem ser agrupadas para evitar repetição.
3. Rótulos já aplicados não devem ser sugeridos novamente.
4. Rótulos rejeitados recentemente devem ter penalização.
5. Rótulos de pessoa podem influenciar reunião, mas não devem ser aplicados à reunião sem evidência adicional.
6. Rótulos de cliente podem influenciar reunião, mas devem indicar se vieram do cliente ou do conteúdo falado.
7. Rótulos sensíveis devem exigir confirmação manual.

## 6.6. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `label` | Cadastro de rótulos | id, name, type, color, status |
| `label_assignment` | Aplicação de rótulo | label_id, entity_type, entity_id, source, confidence |
| `label_suggestion` | Sugestão pendente | label_id, entity_type, entity_id, confidence, reason, status |
| `label_feedback` | Feedback local | suggestion_id, action, user_id, reason, created_at |
| `label_rule` | Regra local opcional | condition, label_id, priority, enabled |

---

# 7. Detector de oportunidades comerciais

## 7.1. Objetivo

Identificar sinais de oportunidade comercial nas reuniões e consolidá-los em uma visão local por cliente.

A ferramenta deve ajudar a consultoria a perceber demandas, dores e possibilidades de expansão que aparecem nas conversas, mesmo quando não são formalizadas como oportunidade.

## 7.2. O que é uma oportunidade comercial

Uma oportunidade comercial é qualquer evidência de que o cliente pode precisar de:

- novo projeto;
- extensão de escopo;
- melhoria de processo;
- automação;
- consultoria adicional;
- diagnóstico;
- treinamento;
- suporte recorrente;
- governança;
- integração;
- relatório;
- migração;
- sustentação;
- revisão de arquitetura;
- implantação de ferramenta;
- melhoria em uma solução existente.

## 7.3. Categorias iniciais de oportunidade

Categorias sugeridas para uma consultoria como a Bizapp:

| Categoria | Sinais comuns |
|---|---|
| Automação de processos | processo manual, aprovação por e-mail, planilha, retrabalho |
| Power Platform | Power Apps, Power Automate, CoE, conectores, ambientes |
| BI e dados | dashboard, indicador, relatório, falta de visibilidade |
| CRM/Dynamics | funil, oportunidade, vendedores, cadastro de clientes, pipeline |
| Integração | ERP, API, sistema legado, sincronização, duplicidade de dados |
| Governança | controle, segurança, política, permissão, auditoria, DLP |
| Treinamento e adoção | usuários não usam, resistência, baixa adoção, capacitação |
| Suporte recorrente | sustentação, evolução contínua, backlog de melhorias |
| Migração | dados legados, troca de sistema, importação, saneamento |
| Assessment | diagnóstico, levantamento, revisão de maturidade |
| Expansão de escopo | nova área, novo processo, nova filial, novo grupo de usuários |

As categorias devem ser configuráveis para se adaptar ao portfólio real da consultoria.

## 7.4. Requisitos funcionais

### F4-OPP-001 — Detectar oportunidade a partir da transcrição

Após processar uma reunião, a ferramenta deve analisar a transcrição localmente e sugerir possíveis oportunidades.

Cada sugestão deve conter:

- título;
- categoria;
- cliente;
- reunião de origem;
- trecho de evidência;
- timestamp;
- pessoa associada, se possível;
- rótulos sugeridos;
- confiança;
- impacto sugerido;
- esforço percebido, quando inferível;
- próxima ação sugerida;
- status inicial.

### F4-OPP-002 — Exibir oportunidades em fila de revisão

O usuário deve revisar oportunidades antes de confirmá-las.

A fila deve permitir:

- aceitar;
- rejeitar;
- editar;
- vincular a cliente;
- vincular a projeto;
- vincular a pessoa;
- criar pendência de follow-up;
- criar rótulo;
- marcar como duplicada;
- transformar em mudança de escopo;
- transformar em risco, se a sugestão foi classificada incorretamente.

### F4-OPP-003 — Central de oportunidades por cliente

Cada cliente deve ter uma visão de oportunidades.

Campos sugeridos:

- título;
- categoria;
- status;
- origem;
- data da primeira menção;
- última menção;
- pessoas relacionadas;
- reuniões relacionadas;
- evidências;
- valor estimado, opcional;
- prioridade;
- probabilidade, opcional;
- responsável interno;
- próxima ação;
- prazo para follow-up;
- rótulos.

### F4-OPP-004 — Agrupar oportunidades semelhantes

Quando uma mesma oportunidade aparecer em várias reuniões, a ferramenta deve sugerir agrupamento.

Exemplo:

- Reunião 1: cliente menciona processo manual de aprovação.
- Reunião 2: cliente menciona demora na aprovação por e-mail.
- Reunião 3: cliente pede rastreabilidade de aprovações.

A ferramenta pode agrupar como:

> Oportunidade: automação do fluxo de aprovação.

### F4-OPP-005 — Sugerir próxima ação comercial

Para cada oportunidade confirmada, a ferramenta deve sugerir uma próxima ação.

Exemplos:

- agendar discovery específico;
- levantar processo atual;
- solicitar exemplos de planilha;
- envolver especialista técnico;
- criar estimativa preliminar;
- preparar proposta;
- validar orçamento;
- mapear decisores;
- criar diagnóstico.

### F4-OPP-006 — Detectar oportunidade a partir de pendências e riscos

O sistema deve conseguir identificar oportunidades derivadas de padrões.

Exemplo:

- Muitas pendências sobre permissões e ambientes podem indicar oportunidade de governança.
- Riscos recorrentes de planilha manual podem indicar oportunidade de automação.
- Discussões frequentes sobre dados inconsistentes podem indicar oportunidade de BI ou saneamento de dados.

## 7.5. Status sugeridos

```text
sugerida
em_revisao
confirmada
em_qualificacao
follow_up_agendado
proposta_em_preparacao
proposta_enviada
ganha
perdida
descartada
duplicada
```

A ferramenta local não precisa substituir o CRM. Ela pode exportar ou publicar em ferramenta externa opcionalmente, mas deve manter seu próprio registro local.

## 7.6. Regras de negócio

1. Nenhuma oportunidade deve ser criada como confirmada sem revisão, salvo configuração explícita.
2. Toda oportunidade deve ter ao menos uma evidência.
3. Oportunidades semelhantes devem ser agrupáveis.
4. Uma oportunidade pode estar associada a múltiplas reuniões.
5. Uma oportunidade pode gerar uma pendência de follow-up.
6. Uma oportunidade pode ser convertida em mudança de escopo quando estiver relacionada ao projeto atual.
7. A rejeição deve ser registrada para melhorar futuras classificações.

## 7.7. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `commercial_opportunity` | Oportunidade local | id, client_id, title, category, status, priority |
| `opportunity_evidence` | Evidências | opportunity_id, meeting_id, transcript_segment_id, quote, confidence |
| `opportunity_person` | Pessoas relacionadas | opportunity_id, person_id, relation_type |
| `opportunity_follow_up` | Próximas ações | opportunity_id, action_item_id |
| `opportunity_status_history` | Histórico | opportunity_id, old_status, new_status, user_id, date |

---

# 8. Detector de riscos e mudanças de escopo

## 8.1. Objetivo

Identificar sinais de risco operacional, comercial, técnico ou de projeto nas reuniões e detectar possíveis mudanças de escopo antes que se tornem problemas.

A ferramenta deve apoiar gerentes, consultores e lideranças a enxergar:

- riscos recorrentes;
- bloqueios;
- decisões pendentes;
- solicitações fora do escopo;
- mudanças de prioridade;
- aumento de esforço;
- dependências de terceiros;
- ausência de responsáveis;
- desalinhamento de expectativas.

## 8.2. Tipos de risco

Categorias iniciais:

| Categoria | Exemplos de sinais |
|---|---|
| Prazo | prazo agressivo, atraso, dependência sem data, urgência |
| Escopo | nova solicitação, ampliação, mudança de requisito, retrabalho |
| Orçamento | falta de verba, aprovação financeira, discussão de custo |
| Técnico | integração complexa, limitação de ferramenta, arquitetura incerta |
| Acesso/Ambiente | falta de permissão, ambiente não criado, bloqueio de segurança |
| Dados | dados incompletos, qualidade baixa, migração incerta |
| Adoção | usuário não engaja, resistência, baixa participação |
| Stakeholder | decisor ausente, conflito entre áreas, troca de responsável |
| Compliance/Jurídico | aprovação jurídica, regra regulatória, dados sensíveis |
| Terceiros | dependência de fornecedor, ERP, consultoria externa |
| Comunicação | falta de alinhamento, decisões não registradas, expectativa diferente |

## 8.3. Tipos de mudança de escopo

Categorias iniciais:

| Tipo | Exemplo |
|---|---|
| Nova área envolvida | incluir área de Compras no projeto |
| Novo processo | automatizar também o fluxo de reembolso |
| Nova integração | integrar com ERP, RH ou sistema legado |
| Novo relatório | criar dashboard executivo adicional |
| Novo perfil de usuário | incluir gestores regionais |
| Mudança de prazo | antecipar entrega ou alterar fase |
| Mudança de prioridade | trocar ordem das entregas |
| Mudança de regra de negócio | alterar aprovação, alçadas ou validações |
| Mudança de volume | mais usuários, mais unidades, mais dados |
| Reprocessamento/retrabalho | refazer tela, fluxo, relatório ou integração |

## 8.4. Requisitos funcionais

### F4-RSC-001 — Detectar risco a partir da transcrição

A ferramenta deve sugerir riscos quando encontrar sinais relevantes na reunião.

Cada risco sugerido deve conter:

- título;
- categoria;
- cliente;
- projeto, se houver;
- reunião de origem;
- trecho de evidência;
- timestamp;
- pessoa relacionada;
- severidade sugerida;
- probabilidade sugerida;
- impacto provável;
- confiança;
- status;
- ação mitigadora sugerida.

### F4-RSC-002 — Detectar mudança de escopo

A ferramenta deve sugerir uma mudança de escopo quando a transcrição indicar uma solicitação nova ou alteração relevante no combinado.

Cada mudança deve conter:

- título;
- tipo de mudança;
- cliente;
- projeto;
- solicitante provável;
- reunião de origem;
- evidência textual;
- impacto sugerido;
- status;
- responsável pela análise;
- prazo de avaliação;
- vínculo com oportunidade, se aplicável;
- vínculo com risco, se aplicável.

### F4-RSC-003 — Fila de revisão de riscos e mudanças

A ferramenta deve apresentar riscos e mudanças sugeridas em uma fila de revisão.

Ações disponíveis:

- confirmar;
- rejeitar;
- editar;
- alterar categoria;
- alterar severidade;
- vincular responsável;
- criar pendência;
- converter risco em mudança de escopo;
- converter mudança de escopo em oportunidade;
- marcar como duplicado;
- vincular a risco existente.

### F4-RSC-004 — Matriz de riscos por cliente

Cada cliente deve ter uma matriz de riscos.

Campos:

- risco;
- categoria;
- severidade;
- probabilidade;
- status;
- responsável;
- data de abertura;
- última atualização;
- reunião de origem;
- evidências;
- ações mitigadoras;
- pendências relacionadas.

### F4-RSC-005 — Controle de mudanças de escopo por cliente/projeto

Cada cliente ou projeto deve ter uma lista de mudanças de escopo.

Campos:

- solicitação;
- origem;
- solicitante;
- impacto;
- status;
- decisão;
- responsável;
- oportunidade relacionada;
- proposta relacionada, se houver;
- data de fechamento.

### F4-RSC-006 — Alertas locais

A ferramenta deve exibir alertas quando houver:

- risco crítico aberto;
- mudança de escopo sem análise;
- muitas mudanças de escopo no mês;
- risco recorrente em várias reuniões;
- pendência relacionada a risco vencida;
- aumento anormal de tempo de reunião com o cliente acompanhado de riscos.

## 8.5. Status sugeridos para riscos

```text
sugerido
em_revisao
ativo
mitigado
aceito
resolvido
descartado
duplicado
```

## 8.6. Status sugeridos para mudanças de escopo

```text
sugerida
em_analise
aguardando_cliente
aprovada
rejeitada
virou_oportunidade
virou_aditivo
descartada
duplicada
```

## 8.7. Regras de negócio

1. Todo risco ou mudança deve ter evidência.
2. Riscos críticos devem aparecer na central do cliente.
3. Mudanças de escopo confirmadas devem poder gerar pendência de avaliação.
4. Mudanças de escopo podem virar oportunidade comercial.
5. O usuário deve poder ajustar severidade, probabilidade e impacto.
6. Riscos rejeitados devem alimentar feedback local.
7. Riscos e mudanças devem ser exportáveis em relatório local.
8. A ferramenta deve diferenciar risco real de simples menção genérica.

## 8.8. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `project_risk` | Risco do cliente/projeto | id, client_id, category, severity, probability, status |
| `risk_evidence` | Evidências do risco | risk_id, meeting_id, segment_id, quote, confidence |
| `risk_mitigation_action` | Ações mitigadoras | risk_id, action_item_id, status |
| `scope_change` | Mudança de escopo | id, client_id, project_id, title, type, status |
| `scope_change_evidence` | Evidências da mudança | scope_change_id, meeting_id, segment_id, quote |
| `scope_change_decision` | Decisões | scope_change_id, decision, decided_by, decided_at |

---

# 9. Central de pendências por cliente

## 9.1. Objetivo

Criar uma visão consolidada de todas as pendências relacionadas a cada cliente, independentemente da reunião onde surgiram.

A central deve ajudar a responder:

- O que está pendente com este cliente?
- Quem ficou responsável?
- O que está vencido?
- Quais pendências vieram de riscos?
- Quais pendências vieram de oportunidades?
- Quais decisões estão aguardando retorno?
- O que deve ser cobrado no próximo follow-up?
- Quais pendências se repetem entre reuniões?

## 9.2. Fontes de pendências

Pendências podem ser criadas a partir de:

- extração automática da transcrição;
- criação manual;
- decisão que exige ação posterior;
- risco que exige mitigação;
- mudança de escopo que exige análise;
- oportunidade que exige follow-up;
- reunião recorrente de status;
- importação opcional de conector externo;
- revisão de ata;
- comentário do usuário.

## 9.3. Tipos de pendência

Tipos sugeridos:

- ação;
- follow-up;
- decisão pendente;
- bloqueio;
- validação;
- aprovação;
- envio de material;
- análise técnica;
- retorno do cliente;
- retorno interno;
- mitigação de risco;
- avaliação de escopo;
- oportunidade comercial;
- preparação de proposta;
- documentação.

## 9.4. Requisitos funcionais

### F4-PEN-001 — Criar pendências automaticamente

A ferramenta deve sugerir pendências a partir da transcrição.

Cada sugestão deve conter:

- título;
- descrição;
- cliente;
- reunião de origem;
- trecho de evidência;
- timestamp;
- responsável sugerido;
- tipo de responsável: `interno`, `cliente`, `não identificado`;
- prazo sugerido, se houver;
- prioridade sugerida;
- rótulos;
- confiança;
- status.

### F4-PEN-002 — Criar pendências manualmente

O usuário deve poder criar uma pendência manualmente.

Campos:

- título;
- descrição;
- cliente;
- projeto;
- responsável;
- prazo;
- prioridade;
- origem;
- rótulos;
- vínculo com reunião;
- vínculo com risco;
- vínculo com oportunidade;
- vínculo com mudança de escopo.

### F4-PEN-003 — Visualizar pendências por cliente

A central deve ter uma visão por cliente com:

- pendências abertas;
- pendências vencidas;
- pendências concluídas;
- pendências sem responsável;
- pendências sem prazo;
- pendências aguardando cliente;
- pendências internas;
- pendências relacionadas a risco;
- pendências relacionadas a oportunidade;
- pendências relacionadas a escopo.

### F4-PEN-004 — Visão consolidada geral

Além da visão por cliente, deve existir uma visão geral.

Filtros:

- cliente;
- projeto;
- responsável;
- origem;
- tipo;
- status;
- prioridade;
- vencimento;
- rótulo;
- reunião;
- risco;
- oportunidade;
- mudança de escopo.

### F4-PEN-005 — Status de pendência

Status sugeridos:

```text
sugerida
em_revisao
aberta
em_andamento
aguardando_cliente
aguardando_interno
bloqueada
concluida
cancelada
descartada
duplicada
```

### F4-PEN-006 — Agrupamento de pendências repetidas

A ferramenta deve detectar pendências semelhantes em reuniões diferentes.

Exemplo:

- Reunião 1: cliente precisa liberar acesso ao ambiente.
- Reunião 2: acesso ainda não liberado.
- Reunião 3: ambiente segue bloqueado.

A ferramenta deve sugerir que se trata da mesma pendência recorrente.

### F4-PEN-007 — Follow-up local

A central deve permitir gerar texto de follow-up localmente.

Formatos:

- texto curto para Teams;
- e-mail;
- ata;
- resumo executivo;
- lista de pendências;
- relatório semanal;
- relatório por cliente.

A publicação em Teams ou envio externo deve ser opcional. A ferramenta deve sempre permitir copiar ou exportar localmente.

### F4-PEN-008 — Priorização de pendências

A prioridade pode considerar:

- prazo vencido;
- risco associado;
- cliente estratégico;
- impacto comercial;
- relação com mudança de escopo;
- dependência de projeto;
- quantidade de reuniões em que a pendência foi repetida;
- responsável não definido;
- bloqueio de próxima etapa.

## 9.5. Campos da pendência

Campos recomendados:

- id;
- cliente;
- projeto;
- título;
- descrição;
- tipo;
- status;
- prioridade;
- responsável sugerido;
- responsável confirmado;
- tipo do responsável;
- data de criação;
- data de vencimento;
- data de conclusão;
- reunião de origem;
- trecho de evidência;
- timestamp;
- rótulos;
- risco relacionado;
- oportunidade relacionada;
- mudança de escopo relacionada;
- confiança da sugestão;
- origem: `manual`, `transcricao`, `risco`, `oportunidade`, `escopo`, `importacao`;
- histórico de alterações.

## 9.6. Indicadores da central de pendências

Por cliente:

- total de pendências abertas;
- pendências vencidas;
- pendências concluídas no mês;
- pendências criadas no mês;
- tempo médio de resolução;
- pendências sem responsável;
- pendências sem prazo;
- pendências recorrentes;
- pendências críticas;
- pendências relacionadas a risco;
- pendências relacionadas a oportunidade.

## 9.7. Regras de negócio

1. Pendências sugeridas devem passar por revisão, salvo configuração de autoaceite.
2. Toda pendência extraída automaticamente deve manter evidência.
3. Pendências concluídas devem permanecer no histórico.
4. Pendências de reuniões excluídas devem ser reavaliadas conforme a política de exclusão.
5. Pendências de reuniões arquivadas podem continuar ativas.
6. Uma pendência pode estar vinculada a múltiplas reuniões.
7. O responsável sugerido deve ser editável.
8. Prazo inferido deve ser exibido como sugestão, não como valor definitivo, até confirmação.

## 9.8. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `action_item` | Pendência | id, client_id, title, status, priority, due_date |
| `action_item_evidence` | Evidência | action_item_id, meeting_id, segment_id, quote |
| `action_item_assignee` | Responsável | action_item_id, person_id, assignment_type, confidence |
| `action_item_relation` | Relações | action_item_id, related_entity_type, related_entity_id |
| `action_item_history` | Histórico | action_item_id, old_value, new_value, changed_by, date |

---

# 10. Indicadores por cliente e tempo de reunião

## 10.1. Objetivo

Criar indicadores objetivos para entender o volume de reuniões por cliente e detectar se o tempo gasto está abaixo, dentro ou acima do padrão histórico.

Esses indicadores devem ajudar a consultoria a perceber:

- clientes com pouco contato recente;
- clientes consumindo tempo acima do normal;
- aumento de reuniões internas sobre um cliente;
- queda de interação com cliente ativo;
- excesso de reuniões sem redução de pendências;
- reuniões recorrentes sem decisões;
- possível risco operacional por aumento de tempo;
- oportunidade comercial por aumento de conversas sobre novas demandas.

## 10.2. Tipos de reunião para indicador

A ferramenta deve classificar reuniões, manual ou automaticamente, em tipos como:

| Tipo | Descrição |
|---|---|
| Cliente externa | Reunião com participação do cliente |
| Interna sobre cliente | Reunião interna da consultoria relacionada ao cliente |
| Interna geral | Reunião interna sem cliente específico |
| Comercial | Reunião de oportunidade, pré-venda ou proposta |
| Projeto | Reunião de execução, status, alinhamento ou entrega |
| Suporte | Reunião de sustentação ou incidente |
| Governança | Reunião executiva, comitê ou acompanhamento |
| Workshop | Sessão de levantamento, desenho ou validação |

A classificação pode usar:

- participantes;
- rótulos;
- título;
- cliente associado;
- origem da reunião;
- transcrição;
- confirmação do usuário.

## 10.3. Indicadores principais

### F4-IND-001 — Tempo de reunião com cliente na semana

Total de tempo em reuniões externas com determinado cliente na semana atual.

Exemplo:

```text
Cliente XPTO
Semana atual: 5h30 em reuniões com cliente
Padrão semanal: 3h40
Status: acima do padrão
```

### F4-IND-002 — Tempo de reunião com cliente no mês

Total de tempo em reuniões externas com determinado cliente no mês atual.

Exemplo:

```text
Cliente XPTO
Mês atual: 18h20 em reuniões com cliente
Padrão mensal: 14h00
Status: dentro do padrão
```

### F4-IND-003 — Tempo de reunião interna sobre cliente na semana

Total de reuniões internas relacionadas ao cliente na semana atual.

Exemplo:

```text
Cliente XPTO
Semana atual: 4h10 em reuniões internas
Padrão semanal interno: 1h30
Status: acima do padrão
Possível leitura: esforço interno elevado ou projeto em fase crítica.
```

### F4-IND-004 — Tempo de reunião interna sobre cliente no mês

Total mensal de reuniões internas relacionadas ao cliente.

Esse indicador é importante para identificar clientes que consomem muito esforço interno mesmo quando o volume de reunião externa não parece alto.

### F4-IND-005 — Quantidade de reuniões por cliente

Quantidade de reuniões por período.

Separar por:

- externas com cliente;
- internas sobre cliente;
- comerciais;
- projeto;
- suporte;
- governança.

### F4-IND-006 — Duração média por reunião

Média e mediana de duração das reuniões do cliente.

A mediana deve ser preferida para análise de padrão, pois reduz impacto de reuniões muito longas fora da curva.

### F4-IND-007 — Variação em relação ao padrão

Comparar o período atual com o padrão histórico do cliente.

Status sugeridos:

```text
sem_dados_suficientes
abaixo_do_normal
ligeiramente_abaixo
dentro_do_padrao
ligeiramente_acima
acima_do_normal
muito_acima_do_normal
```

### F4-IND-008 — Tempo desde a última reunião

Indicar há quantos dias não há reunião com o cliente.

Exemplo:

```text
Última reunião com cliente: 12 dias atrás
Padrão de contato: semanal
Status: abaixo do normal
```

### F4-IND-009 — Relação entre tempo de reunião e pendências

Comparar tempo de reunião com evolução das pendências.

Exemplos de sinais:

- muito tempo de reunião e pendências não reduzem;
- muitas reuniões e poucas decisões;
- pouco tempo de reunião e muitas pendências vencidas;
- aumento de reuniões internas após risco crítico.

### F4-IND-010 — Relação entre tempo de reunião e oportunidades

Detectar clientes com aumento de reuniões associado a oportunidades comerciais.

Exemplo:

```text
O tempo de reunião com o cliente aumentou 65% nas últimas 4 semanas e foram detectadas 3 novas oportunidades comerciais.
```

### F4-IND-011 — Relação entre tempo de reunião e riscos

Detectar clientes com aumento de reuniões associado a riscos.

Exemplo:

```text
O tempo de reunião interna sobre o cliente está 120% acima do padrão e há 2 riscos críticos ativos.
```

## 10.4. Cálculo de padrão histórico

A ferramenta deve calcular o padrão por cliente, pois cada cliente tem comportamento diferente.

### Padrão semanal

Sugestão inicial:

- considerar as últimas 8 semanas completas;
- excluir a semana atual;
- calcular mediana de horas semanais;
- calcular também média, mínimo, máximo e desvio;
- usar mediana como referência principal;
- ignorar semanas sem contrato ativo, se essa informação existir;
- permitir ajuste manual do período de referência.

### Padrão mensal

Sugestão inicial:

- considerar os últimos 6 meses completos;
- excluir o mês atual;
- calcular mediana de horas mensais;
- calcular média, mínimo, máximo e desvio;
- usar mediana como referência principal;
- permitir configuração por cliente.

### Clientes novos

Para clientes com pouco histórico:

- exibir `sem dados suficientes`;
- usar padrão do tipo de cliente/projeto, se configurado;
- usar meta manual cadastrada;
- exibir indicador como experimental;
- não gerar alerta forte sem histórico suficiente.

### Períodos especiais

Alguns períodos podem naturalmente ter mais reuniões:

- discovery;
- kickoff;
- go-live;
- incidente crítico;
- fechamento de proposta;
- homologação;
- virada de fase;
- comitê executivo.

A ferramenta deve permitir marcar período como especial para não gerar interpretação incorreta.

## 10.5. Classificação de status

Parâmetros sugeridos:

```text
Abaixo do normal: menor que 70% do padrão
Ligeiramente abaixo: entre 70% e 85% do padrão
Dentro do padrão: entre 85% e 115% do padrão
Ligeiramente acima: entre 115% e 130% do padrão
Acima do normal: entre 130% e 200% do padrão
Muito acima do normal: maior que 200% do padrão
```

Esses limites devem ser configuráveis globalmente e por cliente.

Exemplo semanal:

```text
Padrão semanal do cliente: 4h00
Semana atual: 2h20
Percentual do padrão: 58%
Status: abaixo do normal
```

Exemplo mensal:

```text
Padrão mensal do cliente: 16h00
Mês atual: 19h00
Percentual do padrão: 119%
Status: ligeiramente acima
```

## 10.6. Separação entre reunião externa e interna

A ferramenta deve separar:

### Tempo com cliente

Reuniões onde o cliente participou.

Exemplos:

- status report com cliente;
- workshop;
- discovery;
- alinhamento executivo;
- homologação;
- suporte com usuário.

### Tempo interno sobre cliente

Reuniões internas da consultoria relacionadas ao cliente.

Exemplos:

- alinhamento interno do projeto XPTO;
- preparação de proposta XPTO;
- análise técnica sobre integração XPTO;
- reunião de mitigação de risco XPTO;
- preparação de workshop.

### Por que essa separação importa

Um cliente pode parecer normal no tempo externo, mas exigir esforço interno alto.

Exemplo:

```text
Tempo com cliente: dentro do padrão
Tempo interno sobre cliente: muito acima do normal
Leitura possível: cliente está gerando esforço interno excessivo, risco técnico ou retrabalho.
```

Também pode ocorrer o inverso:

```text
Tempo com cliente: abaixo do normal
Tempo interno sobre cliente: dentro do padrão
Leitura possível: equipe está trabalhando, mas há pouco alinhamento com o cliente.
```

## 10.7. Indicadores adicionais recomendados

### Indicadores de relacionamento

- dias desde última reunião com cliente;
- frequência média de contato;
- quantidade de stakeholders ativos;
- stakeholders ausentes nas últimas reuniões;
- presença do decisor em reuniões críticas;
- participação do ponto focal.

### Indicadores de produtividade de reunião

- decisões por hora de reunião;
- pendências criadas por hora;
- pendências concluídas por período;
- reuniões sem decisão;
- reuniões sem pendência clara;
- reuniões com muitos assuntos abertos;
- reuniões recorrentes sobre o mesmo bloqueio.

### Indicadores de esforço interno

- tempo interno por cliente;
- tempo interno por oportunidade;
- tempo interno por risco;
- tempo interno sem reunião externa associada;
- relação tempo interno versus tempo com cliente;
- consultores mais envolvidos.

### Indicadores comerciais

- oportunidades novas no mês;
- oportunidades por cliente;
- oportunidades por categoria;
- oportunidades sem follow-up;
- oportunidades com mais de uma evidência;
- oportunidades associadas a aumento de reuniões.

### Indicadores de risco

- riscos ativos;
- riscos críticos;
- riscos sem mitigação;
- riscos recorrentes;
- mudanças de escopo abertas;
- mudanças de escopo sem decisão;
- pendências vencidas associadas a risco.

## 10.8. Dashboard por cliente

A página do cliente deve conter cards como:

```text
Cliente XPTO

Tempo com cliente nesta semana: 5h30 — acima do padrão
Tempo com cliente neste mês: 18h20 — dentro do padrão
Tempo interno nesta semana: 4h10 — muito acima do padrão
Tempo interno neste mês: 9h40 — acima do padrão
Última reunião com cliente: há 2 dias
Pendências abertas: 12
Pendências vencidas: 3
Riscos ativos: 4
Mudanças de escopo abertas: 2
Oportunidades comerciais: 3
Stakeholders ativos: 8
Status operacional sugerido: atenção
```

Cada card deve permitir abrir a lista de reuniões, pendências ou evidências que compõem o número.

## 10.9. Alertas locais

Alertas sugeridos:

- cliente sem reunião há mais tempo que o padrão;
- tempo de reunião com cliente abaixo do normal;
- tempo de reunião com cliente muito acima do normal;
- tempo interno sobre cliente muito acima do normal;
- aumento de reuniões + aumento de riscos;
- aumento de reuniões + mudança de escopo;
- muitas pendências abertas e pouco tempo de reunião;
- muitas reuniões e nenhuma decisão registrada;
- oportunidade identificada sem follow-up;
- risco crítico sem pendência de mitigação.

Os alertas devem ser locais e configuráveis.

## 10.10. Regras de cálculo

1. Reuniões excluídas não devem entrar nos indicadores.
2. Reuniões arquivadas devem continuar no histórico por padrão, mas o usuário pode configurar exclusão de arquivadas dos painéis operacionais.
3. Reuniões sem cliente associado não devem entrar em indicadores por cliente até serem classificadas.
4. Reuniões com múltiplos clientes devem permitir rateio manual ou distribuição proporcional configurável.
5. Reuniões internas devem exigir associação explícita ou sugerida a um cliente.
6. Duração deve vir preferencialmente de metadados do áudio/vídeo; se não existir, pode ser estimada pelos timestamps da transcrição.
7. O padrão histórico deve ser recalculado quando reunião for criada, editada, arquivada, excluída ou reclassificada.
8. Períodos marcados como especiais podem ser excluídos do cálculo de padrão.
9. Indicadores devem mostrar a data de atualização.
10. Todo alerta deve permitir ver a base de cálculo.

## 10.11. Entidades sugeridas

| Entidade | Finalidade | Campos principais |
|---|---|---|
| `meeting_metric` | Métricas da reunião | meeting_id, duration_minutes, meeting_type, client_id |
| `client_period_metric` | Métricas agregadas | client_id, period_type, period_start, external_minutes, internal_minutes |
| `client_metric_baseline` | Padrão histórico | client_id, metric_name, baseline_value, period_window |
| `client_metric_alert` | Alertas | client_id, metric_name, status, severity, created_at |
| `meeting_client_allocation` | Rateio multi-cliente | meeting_id, client_id, allocation_percent |
| `special_period` | Período especial | client_id, start_date, end_date, reason, exclude_from_baseline |

---

# 11. Experiência do usuário

## 11.1. Página inicial da Fase 4

A página inicial deve destacar:

- clientes com alertas;
- pendências vencidas;
- riscos críticos;
- oportunidades novas;
- mudanças de escopo em análise;
- pessoas pendentes de identificação;
- rótulos sugeridos pendentes;
- clientes acima ou abaixo do padrão de reunião.

## 11.2. Workspace do cliente

Cada cliente deve ter uma área consolidada.

Abas sugeridas:

1. **Visão geral**
2. **Reuniões**
3. **Stakeholders**
4. **Pendências**
5. **Riscos**
6. **Mudanças de escopo**
7. **Oportunidades**
8. **Indicadores**
9. **Rótulos**
10. **Histórico**

## 11.3. Fila de revisão

A fila de revisão deve concentrar sugestões da IA local.

Tipos de item:

- pessoa sugerida;
- rótulo sugerido;
- oportunidade sugerida;
- risco sugerido;
- mudança de escopo sugerida;
- pendência sugerida;
- alerta de indicador.

Ações comuns:

- aceitar;
- rejeitar;
- editar;
- mesclar;
- vincular a item existente;
- criar novo registro;
- abrir evidência;
- aplicar em lote.

## 11.4. Evidência contextual

Sempre que a ferramenta sugerir algo, a interface deve mostrar:

- trecho da fala;
- timestamp;
- participante provável;
- reunião;
- data;
- cliente;
- rótulos relacionados;
- motivo da sugestão.

---

# 12. Integração opcional com Teams

## 12.1. Usos recomendados

A integração com Teams pode complementar os módulos descritos sem se tornar dependência.

Funcionalidades opcionais:

- importar título da reunião;
- importar data e duração;
- importar participantes;
- importar transcrição, quando disponível;
- importar gravação, quando disponível;
- associar reunião Teams a cliente;
- publicar follow-up no chat da reunião;
- publicar ata aprovada em canal;
- abrir link externo da reunião;
- usar metadados do calendário para melhorar classificação.

## 12.2. O que não deve depender do Teams

Não deve depender do Teams:

- memória de pessoas;
- memória de voz;
- sugestões de rótulo;
- detecção de oportunidade;
- detecção de risco;
- detecção de mudança de escopo;
- central de pendências;
- cálculo de indicadores;
- exportação local;
- busca local.

## 12.3. Fluxo com Teams

1. A reunião ocorre no Teams.
2. O conector opcional importa metadados, gravação ou transcrição.
3. A ferramenta salva os dados localmente.
4. O processamento principal ocorre no núcleo local.
5. O usuário revisa sugestões.
6. O usuário pode copiar/exportar o resultado ou publicar no Teams, se a integração estiver habilitada.

## 12.4. Fluxo sem Teams

1. O usuário envia arquivo de áudio, vídeo ou transcrição.
2. O usuário informa ou confirma cliente, data e participantes.
3. A ferramenta processa localmente.
4. Os mesmos módulos funcionam normalmente.

---

# 13. Modelo de dados consolidado

## 13.1. Entidades centrais

| Entidade | Descrição |
|---|---|
| `client` | Cliente ou conta atendida |
| `project` | Projeto vinculado a cliente |
| `meeting` | Reunião processada |
| `transcript` | Transcrição da reunião |
| `transcript_segment` | Trecho com timestamp e falante |
| `person` | Pessoa identificada ou recorrente |
| `client_stakeholder` | Pessoa associada a cliente/projeto |
| `label` | Rótulo cadastrado |
| `label_assignment` | Rótulo aplicado a entidade |
| `commercial_opportunity` | Oportunidade detectada ou criada |
| `project_risk` | Risco identificado |
| `scope_change` | Mudança de escopo detectada |
| `action_item` | Pendência ou próximo passo |
| `meeting_metric` | Métricas individuais da reunião |
| `client_period_metric` | Indicadores agregados por período |
| `suggestion` | Sugestão genérica revisável |
| `audit_log` | Auditoria de ações relevantes |

## 13.2. Sugestão como entidade genérica

Para evitar criar uma tabela de sugestão separada para cada módulo, pode-se criar uma entidade genérica:

```text
suggestion
- id
- type: label, person_identity, opportunity, risk, scope_change, action_item, metric_alert
- entity_type
- entity_id
- suggested_payload
- confidence
- reason
- evidence_refs
- status: pending, accepted, rejected, edited, dismissed
- created_at
- reviewed_at
- reviewed_by
```

Essa abordagem facilita a criação de uma fila única de revisão.

---

# 14. Pipeline local de processamento

## 14.1. Pipeline após ingestão

```text
Entrada da reunião
→ Normalização de metadados
→ Transcrição local, se necessário
→ Diarização local, se houver áudio
→ Identificação de pessoas recorrentes
→ Associação sugerida a cliente/projeto
→ Sugestão de rótulos
→ Extração de pendências
→ Extração de oportunidades
→ Extração de riscos
→ Extração de mudanças de escopo
→ Atualização da memória de stakeholders
→ Cálculo de indicadores
→ Indexação local
→ Fila de revisão
```

## 14.2. Reprocessamento

A ferramenta deve permitir reprocessar uma reunião quando:

- novos rótulos forem cadastrados;
- uma pessoa for confirmada;
- uma voz for identificada;
- um cliente for corrigido;
- um modelo local for trocado;
- o usuário solicitar nova análise;
- regras forem atualizadas.

O reprocessamento deve preservar decisões manuais anteriores, salvo quando o usuário optar por recalcular tudo.

---

# 15. Permissões e auditoria

## 15.1. Permissões sugeridas

| Ação | Permissão sugerida |
|---|---|
| Ver cliente | `client.view` |
| Editar cliente | `client.edit` |
| Ver pessoas | `person.view` |
| Editar pessoas | `person.edit` |
| Confirmar identidade | `person.identity.confirm` |
| Gerenciar memória de voz | `voice_memory.manage` |
| Aceitar rótulo | `label.assign` |
| Gerenciar rótulos | `label.manage` |
| Confirmar oportunidade | `opportunity.confirm` |
| Editar oportunidade | `opportunity.edit` |
| Confirmar risco | `risk.confirm` |
| Editar risco | `risk.edit` |
| Confirmar mudança de escopo | `scope_change.confirm` |
| Gerenciar pendência | `action_item.manage` |
| Ver indicadores | `metric.view` |
| Configurar indicadores | `metric.configure` |
| Exportar dados | `export.run` |
| Publicar em conector externo | `connector.publish` |

## 15.2. Auditoria obrigatória

Registrar auditoria para:

- confirmação de identidade;
- alteração de pessoa;
- mesclagem de pessoas;
- exclusão de pessoa;
- aceite/rejeição de sugestão;
- criação de oportunidade;
- alteração de status de oportunidade;
- criação de risco;
- alteração de severidade de risco;
- criação de mudança de escopo;
- alteração de status de mudança de escopo;
- criação e conclusão de pendência;
- configuração de cálculo de indicadores;
- exportação de dados;
- publicação externa opcional.

---

# 16. Exportações locais

A ferramenta deve permitir exportar os dados localmente sem depender de plataformas externas.

Formatos sugeridos:

- Markdown;
- PDF;
- DOCX;
- CSV;
- JSON;
- HTML;
- pacote ZIP.

Relatórios sugeridos:

- resumo do cliente;
- mapa de stakeholders;
- relatório de oportunidades;
- matriz de riscos;
- mudanças de escopo;
- central de pendências;
- indicadores semanais;
- indicadores mensais;
- relatório executivo por cliente;
- briefing antes da reunião;
- follow-up pós-reunião.

---

# 17. Tarefas técnicas sugeridas

## 17.1. Épico A — Memória local de pessoas e stakeholders

1. Criar ou evoluir entidade `person`.
2. Criar entidade `client_stakeholder`.
3. Criar associação entre participante de reunião e pessoa.
4. Criar suporte a pessoas temporárias não identificadas.
5. Criar tela de pessoas.
6. Criar perfil da pessoa.
7. Criar mapa de stakeholders por cliente.
8. Criar serviço de sugestão de identidade por metadados.
9. Integrar sugestão de identidade com memória de voz.
10. Criar fluxo de confirmação de identidade.
11. Criar fluxo de correção de identidade.
12. Criar fluxo de mesclagem de pessoas.
13. Criar histórico de aparições da pessoa.
14. Criar indicadores de participação por pessoa.
15. Criar auditoria para alterações de pessoa.

## 17.2. Épico B — Sugestão de rótulos por pessoa, cliente e assunto

1. Revisar modelo de rótulos da Fase 3 para suportar tipos.
2. Criar aplicação de rótulo em múltiplas entidades.
3. Criar serviço de sugestão de rótulos por reunião.
4. Criar serviço de sugestão de rótulos por pessoa.
5. Criar serviço de sugestão de rótulos por cliente.
6. Criar serviço de detecção de assuntos recorrentes.
7. Criar fila de revisão de rótulos.
8. Criar feedback local de aceite/rejeição.
9. Criar regras para evitar duplicidade.
10. Criar evidência de sugestão.
11. Criar filtros por rótulo nas novas telas.
12. Criar testes unitários para sugestão de rótulos.

## 17.3. Épico C — Detector de oportunidades comerciais

1. Definir taxonomia inicial de oportunidades.
2. Criar entidade `commercial_opportunity`.
3. Criar entidade de evidências de oportunidade.
4. Criar serviço local de extração de oportunidades.
5. Criar fila de revisão de oportunidades.
6. Criar tela de oportunidades por cliente.
7. Criar agrupamento de oportunidades semelhantes.
8. Criar vínculo entre oportunidade e pendência.
9. Criar vínculo entre oportunidade e pessoa.
10. Criar sugestão de próxima ação comercial.
11. Criar histórico de status.
12. Criar exportação de oportunidades.
13. Criar testes com transcrições simuladas.

## 17.4. Épico D — Detector de riscos e mudanças de escopo

1. Definir taxonomia inicial de riscos.
2. Definir taxonomia inicial de mudanças de escopo.
3. Criar entidade `project_risk`.
4. Criar entidade `scope_change`.
5. Criar evidências para risco e mudança.
6. Criar serviço local de detecção de riscos.
7. Criar serviço local de detecção de mudanças de escopo.
8. Criar fila de revisão.
9. Criar matriz de riscos por cliente.
10. Criar lista de mudanças de escopo por cliente/projeto.
11. Criar vínculo com pendências.
12. Criar vínculo com oportunidades.
13. Criar alertas locais para riscos críticos.
14. Criar exportação da matriz de riscos.
15. Criar testes de falsos positivos e falsos negativos.

## 17.5. Épico E — Central de pendências por cliente

1. Criar ou evoluir entidade `action_item`.
2. Criar evidências de pendência.
3. Criar responsável sugerido e responsável confirmado.
4. Criar status de pendência.
5. Criar prioridade de pendência.
6. Criar tela geral de pendências.
7. Criar aba de pendências no cliente.
8. Criar filtros avançados.
9. Criar detecção de pendências repetidas.
10. Criar vínculo de pendência com risco.
11. Criar vínculo de pendência com oportunidade.
12. Criar vínculo de pendência com mudança de escopo.
13. Criar geração de follow-up local.
14. Criar exportação de pendências.
15. Criar testes de fluxo completo.

## 17.6. Épico F — Indicadores por cliente e tempo de reunião

1. Criar entidade de métrica por reunião.
2. Criar classificação de tipo de reunião.
3. Criar associação de reunião a cliente.
4. Criar cálculo de tempo semanal por cliente.
5. Criar cálculo de tempo mensal por cliente.
6. Criar separação entre tempo externo com cliente e tempo interno sobre cliente.
7. Criar cálculo de padrão semanal histórico.
8. Criar cálculo de padrão mensal histórico.
9. Criar classificação abaixo/dentro/acima do padrão.
10. Criar configuração de limites globais.
11. Criar configuração de limites por cliente.
12. Criar suporte a períodos especiais.
13. Criar dashboard de indicadores por cliente.
14. Criar alertas locais de desvio.
15. Criar drill-down para reuniões que compõem cada métrica.
16. Criar testes de cálculo com dados históricos.
17. Criar rotina de recálculo após edição, arquivamento ou exclusão.
18. Criar exportação dos indicadores.

## 17.7. Épico G — Integrações opcionais

1. Criar contrato interno para importação de reunião.
2. Permitir que Teams preencha metadados, quando disponível.
3. Permitir importação de participantes do Teams, quando disponível.
4. Permitir importação de duração do Teams, quando disponível.
5. Criar fallback manual para todos os campos.
6. Garantir que o pipeline funcione sem Teams.
7. Criar opção de publicar follow-up no Teams apenas se conector estiver habilitado.
8. Criar auditoria para publicação externa.

## 17.8. Épico H — Testes, qualidade e validação

1. Criar massa de teste com reuniões de cliente.
2. Criar massa de teste com reuniões internas.
3. Criar casos com oportunidades comerciais.
4. Criar casos com riscos reais.
5. Criar casos com falsas menções de risco.
6. Criar casos com mudanças de escopo.
7. Criar casos com pendências repetidas.
8. Criar casos com clientes sem histórico.
9. Criar casos com clientes acima do padrão.
10. Criar casos com clientes abaixo do padrão.
11. Criar testes unitários de cálculo de indicadores.
12. Criar testes de integração do pipeline.
13. Criar testes de interface para fila de revisão.
14. Criar testes de permissões.
15. Criar testes de exportação.

---

# 18. Critérios de aceite

## 18.1. Memória de pessoas

- A ferramenta permite cadastrar pessoas localmente.
- A ferramenta cria pessoas temporárias para falantes não identificados.
- A ferramenta sugere associação de pessoa com base em evidências.
- O usuário consegue confirmar, corrigir e rejeitar identidade.
- O perfil da pessoa mostra reuniões, rótulos, pendências e clientes relacionados.
- O cliente possui mapa de stakeholders.

## 18.2. Rótulos inteligentes

- A ferramenta sugere rótulos para reunião, pessoa, cliente e assunto.
- Toda sugestão mostra confiança e evidência.
- O usuário consegue aceitar, rejeitar e editar sugestões.
- Feedback influencia sugestões futuras.
- Rótulos aplicados aparecem nos filtros e relatórios.

## 18.3. Oportunidades comerciais

- A ferramenta detecta oportunidades a partir de transcrições.
- Oportunidades aparecem em fila de revisão.
- Oportunidades confirmadas aparecem no cliente.
- Cada oportunidade tem evidência.
- Oportunidades podem gerar follow-up.
- Oportunidades semelhantes podem ser agrupadas.

## 18.4. Riscos e mudanças de escopo

- A ferramenta detecta riscos com categoria, severidade e evidência.
- A ferramenta detecta mudanças de escopo com evidência.
- Riscos e mudanças aparecem em fila de revisão.
- O usuário consegue confirmar, rejeitar e editar.
- Riscos críticos aparecem no dashboard do cliente.
- Mudanças de escopo podem virar oportunidade ou pendência.

## 18.5. Central de pendências

- A ferramenta consolida pendências por cliente.
- Pendências podem vir de reunião, risco, oportunidade, escopo ou criação manual.
- O usuário consegue filtrar por status, responsável, prazo e rótulo.
- Pendências vencidas são destacadas.
- Pendências podem gerar follow-up local.

## 18.6. Indicadores por cliente

- A ferramenta calcula tempo de reunião semanal por cliente.
- A ferramenta calcula tempo de reunião mensal por cliente.
- A ferramenta separa tempo externo com cliente e tempo interno sobre cliente.
- A ferramenta calcula padrão histórico por cliente.
- A ferramenta classifica o período como abaixo, dentro ou acima do padrão.
- O usuário consegue abrir as reuniões que compõem cada indicador.
- Reuniões excluídas deixam de ser consideradas.
- Reuniões arquivadas seguem regra configurada.

## 18.7. Operação local

- Todos os módulos funcionam sem conexão externa.
- Conectores opcionais não são obrigatórios.
- Exportações locais funcionam sem internet.
- Dados e sugestões são persistidos localmente.
- Auditoria é registrada localmente.

---

# 19. Priorização recomendada

## Fase 4.1 — Base operacional local

Priorizar:

1. memória local de pessoas;
2. stakeholders por cliente;
3. rótulos por pessoa, cliente e assunto;
4. central de pendências por cliente;
5. indicadores básicos de tempo semanal e mensal.

## Fase 4.2 — Inteligência consultiva

Priorizar:

1. detector de oportunidades;
2. detector de riscos;
3. detector de mudanças de escopo;
4. agrupamento de oportunidades e pendências;
5. alertas locais.

## Fase 4.3 — Gestão executiva

Priorizar:

1. dashboard executivo por cliente;
2. indicadores comparativos;
3. relatórios semanais e mensais;
4. exportações avançadas;
5. integração opcional com Teams para publicar follow-up.

---

# 20. Resultado esperado

Ao final desta evolução, a ferramenta deixará de ser apenas um repositório de transcrições e passará a atuar como uma **memória operacional local da consultoria**.

Ela deverá ajudar a equipe a:

- lembrar quem são as pessoas importantes de cada cliente;
- identificar stakeholders recorrentes;
- sugerir rótulos automaticamente;
- encontrar oportunidades comerciais escondidas nas conversas;
- antecipar riscos;
- controlar mudanças de escopo;
- acompanhar pendências por cliente;
- medir esforço de reunião semanal e mensal;
- perceber clientes abaixo, dentro ou acima do padrão de interação;
- preparar follow-ups, relatórios e briefings com base em dados locais.

A premissa central permanece: **a ferramenta pode conversar com plataformas externas, mas não pode depender delas para operar suas funcionalidades internas**.
