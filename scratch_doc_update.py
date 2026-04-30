import os

def main():
    doc_path = r"c:\PROJETOS\edu-meetlog\DOCUMENTACAO_FASE3.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update section 3
    sec3_old = """### 3.1. Estratégia Implementada
O `ai_engine.py` utiliza buscas baseadas em regex/palavras-chave em modo "fallback" e off-line. Ele escaneia a transcrição gerada pelo pipeline `faster-whisper`.
- As sugestões são salvas na propriedade `suggested_labels` do `meetings.json` imediatamente após o fim do processamento do `queue_worker.py`.
- O usuário é notificado via UI de que a Inteligência artificial encontrou rótulos sugeridos e pode aceitar ou recusar (que remove a sugestão da tela localmente).
- **Endpoint:** `POST /meetings/{meeting_id}/suggest-labels` permite re-calcular ou forçar uma nova sugestão com base nos novos rótulos criados."""

    sec3_new = """### 3.1. Estratégia Implementada
O `ai_engine.py` utiliza agora **Zero-Shot Context Classification** (classificação semântica em português) processada 100% off-line usando o modelo `mDeBERTa-v3` via biblioteca `transformers`.
- Se a biblioteca não estiver instalada (ou houver erro no carregamento), o sistema possui um "fallback seguro" utilizando regex/palavras-chave determinísticas de forma transparente ao usuário.
- O limiar de confiança do modelo está calibrado em 65%.
- As sugestões são salvas na propriedade `suggested_labels` do `meetings.json` imediatamente após o fim do processamento do `queue_worker.py`.
- O usuário é notificado via UI com botões amigáveis ("✓ Aceitar" e "✕ Recusar") para endossar ou rejeitar o contexto da IA.
- **Endpoint:** `POST /meetings/{meeting_id}/suggest-labels` permite re-calcular ou forçar uma nova sugestão com base nos novos rótulos criados."""

    if sec3_old in content:
        content = content.replace(sec3_old, sec3_new)

    # Update Checklist Frontend
    chk_old = """- [x] Menu *dropdown* permite filtrar "Ativas" e "Arquivadas" e também selecionar visualização por um rótulo específico.
- [x] Tela da "Transcrições" renderiza "badges" para cada etiqueta aceita.
- [x] Tela da "Transcrições" mostra *box* de sugestões de IA pendentes com "Aceitar (✓)" e "Recusar (✕)"."""
    
    chk_new = """- [x] Incluído botão global de "Selecionar Tudo" na listagem de reuniões.
- [x] Menu *dropdown* permite filtrar "Ativas" e "Arquivadas" e também selecionar visualização por um rótulo específico.
- [x] Tela da "Transcrições" renderiza "badges" para cada etiqueta aceita.
- [x] Tela da "Transcrições" mostra *box* de sugestões de IA otimizado com espaçamento legível ("✓ Aceitar" e "✕ Recusar").
- [x] Corrigido o design dos controles de janela nativos do Windows ("DarkWindow")."""

    if chk_old in content:
        content = content.replace(chk_old, chk_new)

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
