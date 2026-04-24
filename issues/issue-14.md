## Descrição
Realizar build e criar distribuição do app desktop para Windows.

## Objetivos
- [ ] Build de produção (release build)
- [ ] Gerar executável .exe
- [ ] Testar executável standalone
- [ ] Criar instalador (opcional)
- [ ] Criar release no GitHub

## Build Tauri
```bash
# Development
npm run tauri dev

# Production
npm run tauri build
```

## Saída esperada
```
src-tauri/target/release/
├── edu-meetlog.exe
├── WebView2Loader.dll
└── resources/
```

## Configuração tauri.conf.json
```json
{
  "productName": "Edu MeetLog",
  "version": "1.0.0",
  "identifier": "com.edumeetlog.app",
  "build": {
    "devtools": true
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

## Criar Release no GitHub
```bash
# Criar tag
git tag v1.0.0
git push origin v1.0.0

# Criar release via GitHub CLI
gh release create v1.0.0 \
  --title "Edu MeetLog v1.0.0" \
  --notes "Primeira versão" \
  edu-meetlog.exe
```

## Checklist de pré-build
- [ ] Todos os testes passando
- [ ] Sem warnings de lint
- [ ] Sem erros de typecheck
- [ ] Build completa sem erros
- [ ] Executável inicia corretamente

## Entregáveis
- edu-meetlog.exe (executável)
- (opcional) instalador MSI/NSIS