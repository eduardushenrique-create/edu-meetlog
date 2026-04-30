import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Meetings component signature
    meetings_sig_anchor = """function Meetings({
  meetings,
  onOpen,
  onDelete,
}: {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
  onDelete: (id: string) => void;
}) {"""
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
}: {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
  onDelete: (id: string) => void;
  onBulkDelete?: (ids: string[]) => void;
  onBulkArchive?: (ids: string[]) => void;
  labels?: any[];
  selectedIds?: string[];
  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
}) {"""
    if meetings_sig_anchor in content:
        content = content.replace(meetings_sig_anchor, meetings_sig_replacement)

    # 2. Update Meetings component body to include checkboxes, labels, and bulk action bar
    meetings_body_anchor = """        <button
          className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Exportar todas
        </button>
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {meetings.map((m) => ("""
        
    meetings_body_replacement = """        <div className="flex gap-2">
          {selectedIds && selectedIds.length > 0 && (
            <>
              <button
                className="bg-red-900/50 text-red-400 border border-red-800 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-red-800 transition-colors"
                onClick={() => onBulkDelete?.(selectedIds)}
              >
                Excluir {selectedIds.length}
              </button>
              <button
                className="bg-gray-800 text-gray-300 border border-gray-700 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors"
                onClick={() => onBulkArchive?.(selectedIds)}
              >
                Arquivar {selectedIds.length}
              </button>
              <button
                className="text-gray-500 hover:text-gray-300 text-xs cursor-pointer bg-transparent border-none"
                onClick={() => onClearSelection?.()}
              >
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {meetings.filter(m => !m.archived).map((m) => ("""
    if meetings_body_anchor in content:
        content = content.replace(meetings_body_anchor, meetings_body_replacement)

    # Add Checkbox and Labels to Meeting item
    meeting_item_anchor = """            <div className="flex-1 min-w-0" onClick={() => onOpen(m)}>
              <div
                className="text-sm font-medium text-gray-200 mb-0.5 truncate"
                style={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {m.name}
              </div>
              <div className="flex gap-3 items-center">
                <span className="text-xs text-gray-600">{m.date}</span>
                <span className="text-xs text-gray-700 font-mono">{m.duration}</span>"""
                
    meeting_item_replacement = """            <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
              <input 
                type="checkbox" 
                checked={selectedIds?.includes(m.id) || false} 
                onChange={() => onToggleSelection?.(m.id)}
                className="w-4 h-4 cursor-pointer accent-blue-600"
              />
            </div>
            <div className="flex-1 min-w-0" onClick={() => onOpen(m)}>
              <div
                className="text-sm font-medium text-gray-200 mb-0.5 truncate"
                style={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {m.name}
              </div>
              <div className="flex gap-3 items-center">
                <span className="text-xs text-gray-600">{m.date}</span>
                <span className="text-xs text-gray-700 font-mono">{m.duration}</span>
                {m.labels?.map(lblId => {
                  const lbl = labels?.find(l => l.id === lblId);
                  if (!lbl) return null;
                  return (
                    <span key={lblId} className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: lbl.color + '20', color: lbl.color, border: `1px solid ${lbl.color}40` }}>
                      {lbl.name}
                    </span>
                  );
                })}"""
    if meeting_item_anchor in content:
        content = content.replace(meeting_item_anchor, meeting_item_replacement)


    # 3. Update SettingsPanel signature
    settings_sig_anchor = """function SettingsPanel({
  settings,
  onChange,
  onSave,
  saved,
}: {
  settings: SettingsState;
  onChange: (s: SettingsState) => void;
  onSave: () => void;
  saved: boolean;
}) {"""
    settings_sig_replacement = """function SettingsPanel({
  settings,
  onChange,
  onSave,
  saved,
  labels = [],
  onAddLabel,
  onRemoveLabel
}: {
  settings: SettingsState;
  onChange: (s: SettingsState) => void;
  onSave: () => void;
  saved: boolean;
  labels?: any[];
  onAddLabel?: (name: string, color: string) => void;
  onRemoveLabel?: (id: string) => void;
}) {
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#3b82f6');"""
    if settings_sig_anchor in content:
        content = content.replace(settings_sig_anchor, settings_sig_replacement)

    # 4. Add Labels section to SettingsPanel
    settings_labels_anchor = """      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          ATALHOS
        </div>"""
        
    settings_labels_replacement = """      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          ETIQUETAS (LABELS)
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 mb-2">
            <input 
              type="text" 
              placeholder="Nome da etiqueta" 
              value={newLabelName}
              onChange={(e) => setNewLabelName(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-800 text-gray-200 rounded px-3 py-1.5 text-sm"
            />
            <input 
              type="color" 
              value={newLabelColor}
              onChange={(e) => setNewLabelColor(e.target.value)}
              className="w-8 h-8 rounded border border-gray-800 cursor-pointer p-0 bg-gray-900"
            />
            <button 
              onClick={() => {
                if (newLabelName && onAddLabel) {
                  onAddLabel(newLabelName, newLabelColor);
                  setNewLabelName('');
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded px-3 py-1.5 text-sm font-medium border-none cursor-pointer"
            >
              Adicionar
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {labels.map(l => (
              <div key={l.id} className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium" style={{ background: l.color + '20', color: l.color, border: `1px solid ${l.color}40` }}>
                {l.name}
                <button onClick={() => onRemoveLabel?.(l.id)} className="bg-transparent border-none text-current opacity-70 hover:opacity-100 cursor-pointer p-0 ml-1">
                  &times;
                </button>
              </div>
            ))}
            {labels.length === 0 && <span className="text-xs text-gray-600">Nenhuma etiqueta criada.</span>}
          </div>
        </div>
      </div>

      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          ATALHOS
        </div>"""
    if settings_labels_anchor in content:
        content = content.replace(settings_labels_anchor, settings_labels_replacement)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("App.tsx UI updated successfully with Meetings and SettingsPanel modifications.")

if __name__ == "__main__":
    main()
