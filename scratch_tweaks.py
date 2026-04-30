import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Transcription IA Suggestion Box
    ia_anchor = """                <div className="flex items-center ml-1 gap-2 border-l border-gray-700 pl-2">
                  <button onClick={() => handleAcceptSuggestion(l.id)} className="bg-transparent border-none text-green-500 hover:text-green-400 cursor-pointer p-0 font-bold" title="Aceitar">✓</button>
                  <button onClick={() => handleRejectSuggestion(l.id)} className="bg-transparent border-none text-red-500 hover:text-red-400 cursor-pointer p-0 font-bold" title="Recusar">✕</button>
                </div>"""
                
    ia_replacement = """                <div className="flex items-center ml-3 gap-3 border-l border-gray-700 pl-3">
                  <button onClick={() => handleAcceptSuggestion(l.id)} className="flex items-center gap-1 bg-green-500/10 border border-green-500/20 text-green-500 hover:bg-green-500/20 rounded px-2 py-0.5 cursor-pointer font-bold text-[10px]" title="Aceitar">✓ Aceitar</button>
                  <button onClick={() => handleRejectSuggestion(l.id)} className="flex items-center gap-1 bg-red-500/10 border border-red-500/20 text-red-500 hover:bg-red-500/20 rounded px-2 py-0.5 cursor-pointer font-bold text-[10px]" title="Recusar">✕ Recusar</button>
                </div>"""

    if ia_anchor in content:
        content = content.replace(ia_anchor, ia_replacement)
        
    # 2. Add Select All to Meetings Component
    mtg_sig_anchor = """  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
}) {"""
    mtg_sig_repl = """  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
  onSelectAll?: (ids: string[]) => void;
}) {"""
    if mtg_sig_anchor in content:
        content = content.replace(mtg_sig_anchor, mtg_sig_repl)

    mtg_list_anchor = """      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {filteredMeetings.length === 0 && ("""
    
    mtg_list_repl = """      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {filteredMeetings.length > 0 && (
          <div className="flex items-center p-2 mb-2 bg-gray-900 border border-gray-800 rounded-md">
            <input 
              type="checkbox" 
              checked={selectedIds?.length === filteredMeetings.length && filteredMeetings.length > 0} 
              onChange={(e) => {
                if (e.target.checked) {
                  onSelectAll?.(filteredMeetings.map(m => m.id));
                } else {
                  onClearSelection?.();
                }
              }}
              className="w-4 h-4 cursor-pointer accent-blue-600 mx-1"
            />
            <span className="text-xs text-gray-400 font-medium ml-2">Selecionar Tudo ({filteredMeetings.length})</span>
          </div>
        )}
        {filteredMeetings.length === 0 && ("""

    if mtg_list_anchor in content:
        content = content.replace(mtg_list_anchor, mtg_list_repl)

    # 3. Add handleSelectAll to App component and pass to Meetings
    app_sel_anchor = """  const clearSelection = () => setSelectedIds([]);"""
    app_sel_repl = """  const clearSelection = () => setSelectedIds([]);
  
  const handleSelectAll = (ids: string[]) => {
    setSelectedIds(ids);
  };"""
    if app_sel_anchor in content:
        content = content.replace(app_sel_anchor, app_sel_repl)

    app_mtg_anchor = """            onToggleSelection={toggleSelection}
            onClearSelection={clearSelection}
          />"""
    app_mtg_repl = """            onToggleSelection={toggleSelection}
            onClearSelection={clearSelection}
            onSelectAll={handleSelectAll}
          />"""
    if app_mtg_anchor in content:
        content = content.replace(app_mtg_anchor, app_mtg_repl)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
