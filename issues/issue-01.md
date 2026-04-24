## Descrição
Configurar a estrutura base do projeto com Tauri + React, incluindo dependências e configurações iniciais.

## Objetivos
- [ ] Criar projeto Tauri com React como frontend
- [ ] Configurar TypeScript
- [ ] Configurar TailwindCSS para estilização
- [ ] Configurar estrutura de diretórios do projeto
- [ ] Configurar variáveis de ambiente
- [ ] Verificar build inicial

## Estrutura de diretórios
```
src/
src-tauri/
├── src/
├── icons/
├── Cargo.toml
├── tauri.conf.json
├── build.rs
package.json
tsconfig.json
vite.config.ts
tailwind.config.js
```

## Tecnologias
- **Frontend**: React 18+ com TypeScript
- **Desktop**: Tauri 2.x
- **Estilização**: TailwindCSS
- **Build**: Vite

## Comando para criar projeto
```bash
npm create tauri-app@latest edu-meetlog -- --template react-ts
```

## Referências
- https://tauri.app/start/
- https://react.dev/