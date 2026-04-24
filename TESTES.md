# Testes Ponta a Ponta - Edu MeetLog

## Teste 1: Inicialização do Aplicativo
### Objetivo
Verificar que o aplicativo inicia corretamente sem erros.

### Passos
1. Executar `Edu MeetLog.exe`
2. Verificar abertura da janela principal
3. Verificar carregamento do backend Python
4. Verificar conexão com API interna

### Critérios de Sucesso
- [ ] Janela abre em até 10 segundos
- [ ] Sem erros no console
- [ ] UI carrega corretamente
- [ ] Dashboard exibe status "STOPPED"

---

## Teste 2: Configureação de Microfone
### Objetivo
Verificar que o microfone é configurado e detectado corretamente.

### Passos
1. Abrir Settings
2. Ativar "Microfone"
3. Verificar listagem de dispositivos (opcional)
4. Salvar configurações

### Critérios de Sucesso
- [ ] Toggle ativa corretamente
- [ ] Configuração persiste após reiniciar
- [ ] Micenabled=true no status

---

## Teste 3: Iniciar Gravação
### Objetivo
Verificar que a gravação inicia quando o botão é clicado.

### Passos
1. No Dashboard, clicar "INICIAR"
2. Verificar mudança de status para "RECORDING"
3. Verificar timer começando
4. Verificar botão mudando para "PARAR"

### Critérios de Sucesso
- [ ] Status muda para "RECORDING"
- [ ] Timer incrementa
- [ ] Botão mostra "PARAR"
- [ ] Áudio é captado pelo microfone

---

## Teste 4: Parar Gravação
### Objetivo
Verificar que a gravação para corretamente.

### Passos
1. Com gravação ativa, clicar "PARAR"
2. Verificar mudança de status para "STOPPED"
3. Verificar arquivo WAV criado em recordings/

### Critérios de Sucesso
- [ ] Status muda para "STOPPED"
- [ ] Arquivo WAV criado
- [ ] Duração correta (aproximada)

---

## Teste 5: Segmentação Automática
### Objetivo
Verificar que segmentos de 5 minutos são criados automaticamente.

### Passos
1. Iniciar gravação
2. Aguardar mais de 5 minutos
3. Verificar múltiplos arquivos em recordings/

### Critérios de Sucesso
- [ ] Arquivos criados a cada 5 min
- [ ] Timestamps corretos nos nomes
- [ ] Sem perda de áudio

---

## Teste 6: Fila de Processamento
### Objetivo
Verificar que arquivos são movidos para fila de transcrição.

### Passos
1. Parar gravação
2. Verificar arquivos em queue/pending/
3. Aguardar processamento iniciar

### Critérios de Sucesso
- [ ] Arquivos movidos para pending/
- [ ] Status "processing" aparece
- [ ] Status "done" após transcrição

---

## Teste 7: Transcrição de Áudio
### Objetivo
Verificar que o áudio é transcrito corretamente.

### Passos
1.完成 gravação e processamento
2. Ir para Meetings
3. Clicar na reunião
4. Ver transcrição

### Critérios de Sucesso
- [ ] Transcrição gerada
- [ ] Texto em português
- [ ] Timestamps corretos

---

## Teste 8: Hotkey Start/Stop
### Objetivo
Verificar que CTRL+ALT+R alterna gravação.

### Passos
1. Com app em background
2. Pressionar CTRL+ALT+R
3. Verificar mudança de status

### Critérios de Sucesso
- [ ] Gravação inicia se estava parada
- [ ] Gravação para se estava ativa

---

## Teste 9: Hotkey Mostrar App
### Objetivo
Verificar que CTRL+ALT+S mostra a janela.

### Passos
1. Minimizar app
2. Pressionar CTRL+ALT+S
3. Verificar janela visível

### Critérios de Sucesso
- [ ] Janela restaura
- [ ] Janela ganha foco

---

## Teste 10: Persistência de Configurações
### Objetivo
Verificar que configurações sobrevivem reinício.

### Passos
1. Alterar configurações em Settings
2. Salvar
3. Fechar app
4. Abrir app novamente
5. Verificar configurações

### Critérios de Sucesso
- [ ] Configurações mantidas
- [ ] Modelo selectionado persiste
- [ ] Workers configurados

---

## Teste 11: Interface Meetings
### Objetivo
Verificar lista de reuniões.

### Passos
1.完成 algumas gravações
2. Ir para Meetings
3. Ver lista de reuniões

### Critérios de Sucesso
- [ ] Reuniões listadas
- [ ] Data correta
- [ ] Status correto

---

## Teste 12: Interface Transcription
### Objetivo
Verificar visualização de transcrição.

### Passos
1. Clicar em uma reunião
2. Ver transcrição com timestamps
3. Ver speakers

### Critérios de Sucesso
- [ ] Timestamps formato [MM:SS]
- [ ] USER/OTHER identificado
- [ ] Texto legível

---

## Teste 13: Operação Contínua (Curta)
### Objetivo
Verificar estabilidade em operação média.

### Passos
1. Iniciar gravação
2. Deixar por 30 minutos
3. Verificar funcionamento

### Critérios de Sucesso
- [ ] Sem crashes
- [ ] Sem freezes
- [ ] Arquivos criados

---

## Teste 14: Interface Responsiva
### Objetivo
Verificar que UI responde durante gravação.

### Passos
1. Iniciar gravação
2. Navegar entre abas
3. Verificar responsividade

### Critérios de Sucesso
- [ ] Navegação fluida
- [ ] Sem lentidão
- [ ] Timer atualizando

---

## Teste 15: Controle via API
### Objetivo
Verificar API responde corretamente.

### Passos
1. GET /status
2. POST /recording/start
3. POST /recording/stop

### Critérios de Sucesso
- [ ] Status retorna JSON correto
- [ ] Start retorna success
- [ ] Stop retorna success

---

## Teste 16: Tratamento de Erros
### Objetivo
Verificar comportamento em erros.

### Passos
1. Tentar start enquanto gravando
2. Tentar stop sem gravar
3. Verificar mensagens

### Critérios de Sucesso
- [ ] Mensagens de erro claras
- [ ] Sem crash em erros
- [ ] Estado consistente