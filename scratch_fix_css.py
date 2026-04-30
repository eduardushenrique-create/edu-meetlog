import os

def main():
    css_path = r"c:\PROJETOS\edu-meetlog\src\index.css"
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()

    # We will remove traffic lights
    tl_anchor = """.traffic-lights {
  display: flex;
  gap: 7px;
  align-items: center;
  position: absolute;
  right: 14px;
}

.traffic-light {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  opacity: 0.85;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
}

.traffic-light:hover {
  opacity: 1;
  transform: scale(1.1);
}

.traffic-light:active {
  transform: scale(0.95);
}

.dark-window-title {
  display: none;
}"""

    replacement = """.window-controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}

.window-control {
  width: 46px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a0a0a0;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.window-control:hover {
  background: #2a2a2a;
  color: #fff;
}

.window-control.close:hover {
  background: #e81123;
  color: #fff;
}

.dark-window-title {
  display: flex !important;
  align-items: center;
  font-size: 12px;
  color: #888;
}"""

    if tl_anchor in content:
        content = content.replace(tl_anchor, replacement)
        
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Document this in the main doc file
    doc_path = r"c:\PROJETOS\edu-meetlog\📄 DOCUMENTAÇÃO.txt"
    with open(doc_path, "a", encoding="utf-8") as f:
        f.write("\n________________________________________\n")
        f.write("13. DIRETRIZES DE DESIGN\n")
        f.write("• ATENÇÃO ESTRITA: O layout de controles de janela DEVE SEMPRE usar o padrão do Windows (minimizar, maximizar, fechar no canto superior direito com ícones clássicos SVG).\n")
        f.write("• NUNCA utilize o padrão de botões coloridos estilo macOS (traffic-lights vermelhos/amarelos/verdes).\n")
    
    print("CSS and Doc updated")

if __name__ == "__main__":
    main()
