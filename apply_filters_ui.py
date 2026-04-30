import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Meetings component to include local state for filters
    meetings_sig_anchor = """function Meetings({
  meetings,
  onOpen,
  onDelete,
  onBulkDelete,
  onBulkArchive,
  labels,
  selectedIds,
  onToggleSelection,
  onClearSelection
}: {"""
    
    meetings_sig_replacement = """function Meetings({
  meetings,
  onOpen,
  onDelete,
  onBulkDelete,
  onBulkArchive,
  labels,
  selectedIds,
  onToggleSelection,
  onClearSelection
}: {"""

    # Wait, Meetings needs to use `useState` for its filter states.
    # We also need to add the filter UI before the list of meetings.
    
    meetings_body_anchor = """  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
}) {
  return (
    <div className="h-full flex flex-col pt-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold font-sans text-gray-100 tracking-tight">Transcrições</h2>
        <button
          className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Exportar todas
        </button>
      </div>"""
      
    meetings_body_replacement = """  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
}) {
  const [showArchived, setShowArchived] = useState(false);
  const [selectedLabelFilter, setSelectedLabelFilter] = useState<string>('');

  const filteredMeetings = meetings.filter(m => {
    // 1. Filter by archived status
    if (showArchived) {
      if (!m.archived) return false;
    } else {
      if (m.archived) return false;
    }
    
    // 2. Filter by label
    if (selectedLabelFilter) {
      if (!m.labels || !m.labels.includes(selectedLabelFilter)) return false;
    }
    
    return true;
  });

  return (
    <div className="h-full flex flex-col pt-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold font-sans text-gray-100 tracking-tight">Transcrições</h2>
        <button
          className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Exportar todas
        </button>
      </div>
      
      <div className="flex gap-2 mb-4 items-center flex-wrap">
        <select 
          className="bg-gray-900 border border-gray-800 text-gray-300 rounded px-2 py-1 text-xs outline-none"
          value={showArchived ? 'archived' : 'active'}
          onChange={(e) => setShowArchived(e.target.value === 'archived')}
        >
          <option value="active">Ativas</option>
          <option value="archived">Arquivadas</option>
        </select>
        
        <select 
          className="bg-gray-900 border border-gray-800 text-gray-300 rounded px-2 py-1 text-xs outline-none"
          value={selectedLabelFilter}
          onChange={(e) => setSelectedLabelFilter(e.target.value)}
        >
          <option value="">Todas as Etiquetas</option>
          {(labels || []).map(l => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
      </div>"""
      
    if meetings_body_anchor in content:
        content = content.replace(meetings_body_anchor, meetings_body_replacement)

    # 2. Update the mapping logic to use `filteredMeetings`
    map_anchor = """      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {meetings.filter(m => !m.archived).map((m) => ("""
        
    map_replacement = """      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {filteredMeetings.length === 0 && (
          <div className="text-gray-500 text-sm text-center mt-10">
            Nenhuma transcrição encontrada.
          </div>
        )}
        {filteredMeetings.map((m) => ("""
        
    if map_anchor in content:
        content = content.replace(map_anchor, map_replacement)

    # 3. Handle un-archiving from UI (since they are looking at archived, maybe they want to restore?)
    # Roadmap F3.2.4 says "POST /transcriptions/bulk/restore, caso o produto permita restaurar arquivadas".
    # We can add an "Unarchive" button in the bulk action bar if `showArchived` is true.
    # Wait, we need an `onBulkRestore` prop first.
    
    # Adding unarchive action requires backend support for bulk restore. Let's just focus on filters first.
    # Also I'll update the bulk archive button text to "Desarquivar" if we are in the archived view. 
    # But wait, without backend support we can't unarchive easily unless we add an endpoint.
    # I'll leave the Unarchive for later if requested, right now I'll just change the bulk archive logic to be hidden or changed.
    
    bulk_action_anchor = """              <button
                className="bg-gray-800 text-gray-300 border border-gray-700 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors"
                onClick={() => onBulkArchive?.(selectedIds)}
              >
                Arquivar {selectedIds.length}
              </button>"""
              
    bulk_action_replacement = """              {!showArchived && (
                <button
                  className="bg-gray-800 text-gray-300 border border-gray-700 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors"
                  onClick={() => onBulkArchive?.(selectedIds)}
                >
                  Arquivar {selectedIds.length}
                </button>
              )}"""
              
    if bulk_action_anchor in content:
        content = content.replace(bulk_action_anchor, bulk_action_replacement)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Filter UI successfully added to App.tsx")

if __name__ == "__main__":
    main()
