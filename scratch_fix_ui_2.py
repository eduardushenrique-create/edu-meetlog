import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace DarkWindow
    dw_anchor = """function DarkWindow({ children }: { children: ReactNode }) {
  return (
    <div className="dark-window">
      <div className="dark-window-titlebar">
        <div className="traffic-lights">
          {['#ef4444', '#f59e0b', '#22c55e'].map((color) => {
            const isClose = color === '#ef4444';
            const isMinimize = color === '#f59e0b';
            const isMaximize = color === '#22c55e';
            const action = isClose ? window.electronAPI?.closeWindow :
                           isMinimize ? window.electronAPI?.minimizeWindow :
                           isMaximize ? window.electronAPI?.maximizeWindow : undefined;
            return <span key={color} className="traffic-light" style={{ background: color, cursor: 'pointer' }} onClick={action} />
          })}
        </div>
        <div className="dark-window-title">Edu MeetLog</div>
      </div>
      <div className="dark-window-content">{children}</div>
    </div>
  );
}"""

    dw_replacement = """function DarkWindow({ children }: { children: ReactNode }) {
  return (
    <div className="dark-window">
      <div className="dark-window-titlebar" style={{ display: 'flex', justifyContent: 'space-between', paddingRight: '0' }}>
        <div className="dark-window-title" style={{ paddingLeft: '12px' }}>Edu MeetLog</div>
        <div className="window-controls" style={{ display: 'flex', height: '100%' }}>
          <div className="window-control minimize" onClick={window.electronAPI?.minimizeWindow} title="Minimizar">
            <svg viewBox="0 0 10 1" width="10" height="1"><path d="M0,0 L10,0" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
          <div className="window-control maximize" onClick={window.electronAPI?.maximizeWindow} title="Maximizar">
            <svg viewBox="0 0 10 10" width="10" height="10"><path d="M0,0 L10,0 L10,10 L0,10 Z" fill="none" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
          <div className="window-control close" onClick={window.electronAPI?.closeWindow} title="Fechar">
            <svg viewBox="0 0 10 10" width="10" height="10"><path d="M0,0 L10,10 M10,0 L0,10" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
        </div>
      </div>
      <div className="dark-window-content">{children}</div>
    </div>
  );
}"""

    if dw_anchor in content:
        content = content.replace(dw_anchor, dw_replacement)
    else:
        print("Could not find DarkWindow anchor")

    # 2. Replace Meetings
    mtg_anchor = """}) {
  return (
    <div className="h-full flex flex-col" style={{ padding: '28px 32px' }}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold">REUNIÕES</div>
          <div className="text-lg font-semibold mt-0.5">{meetings.length} gravações</div>
        </div>
        <div className="flex gap-2">"""

    mtg_replacement = """}) {
  const [showArchived, setShowArchived] = useState(false);
  const [filterLabel, setFilterLabel] = useState<string>('');

  const filteredMeetings = meetings.filter(m => {
    if (showArchived && !m.archived) return false;
    if (!showArchived && m.archived) return false;
    if (filterLabel && !(m.labels || []).includes(filterLabel)) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col" style={{ padding: '28px 32px' }}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold">REUNIÕES</div>
          <div className="text-lg font-semibold mt-0.5">{filteredMeetings.length} gravações</div>
        </div>
        <div className="flex gap-2 items-center">
          <select 
            className="bg-transparent border border-gray-700 text-gray-400 rounded px-2 py-1 text-xs outline-none cursor-pointer"
            value={showArchived ? 'archived' : 'active'}
            onChange={(e) => setShowArchived(e.target.value === 'archived')}
          >
            <option value="active">Ativas</option>
            <option value="archived">Arquivadas</option>
          </select>
          <select 
            className="bg-transparent border border-gray-700 text-gray-400 rounded px-2 py-1 text-xs outline-none cursor-pointer"
            value={filterLabel}
            onChange={(e) => setFilterLabel(e.target.value)}
          >
            <option value="">Todas as Etiquetas</option>
            {(labels || []).map(l => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>"""

    if mtg_anchor in content:
        content = content.replace(mtg_anchor, mtg_replacement)
    else:
        print("Could not find Meetings anchor")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed UI applied")

if __name__ == "__main__":
    main()
