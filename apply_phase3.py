import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Tab
    content = content.replace(
        "type Tab = 'dashboard' | 'meetings' | 'transcription' | 'settings';",
        "type Tab = 'dashboard' | 'meetings' | 'transcription' | 'settings' | 'calendar';"
    )

    # 2. Add state variables
    state_anchor = """  const [realtimeSegments, setRealtimeSegments] = useState<Segment[]>([]);
  const [wsConnected, setWsConnected] = useState(false);"""
    
    state_replacement = """  const [realtimeSegments, setRealtimeSegments] = useState<Segment[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [labels, setLabels] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };"""
    content = content.replace(state_anchor, state_replacement)

    # 3. Add performPauseResume and update performToggle
    toggle_anchor = """      fetchStatus();
      if (current) {
        fetchMeetings();
      } else {
        setRealtimeSegments([]);
      }
    } catch (e) {
      console.error('Error in performToggle:', e);
    }
  };"""
  
    toggle_replacement = """      const data = await res.json();
      if (data.success) {
        showToast(current ? 'Gravação finalizada com sucesso!' : 'Gravação iniciada!', 'success');
      } else {
        showToast(data.message || 'Erro na operação', 'error');
      }
      
      fetchStatus();
      if (current) {
        fetchMeetings();
      } else {
        setRealtimeSegments([]);
      }
    } catch (e) {
      console.error('Error in performToggle:', e);
      showToast('Falha na comunicação com o servidor local', 'error');
    }
  };

  const performPauseResume = async () => {
    try {
      const endpoint = isPaused ? 'resume' : 'pause';
      const res = await fetch(`${API_URL}/recording/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast(isPaused ? 'Gravação continuada' : 'Gravação pausada', 'success');
        setIsPaused(!isPaused);
      } else {
        showToast(data.message || 'Erro ao alterar estado', 'error');
      }
      fetchStatus();
    } catch (e) {
      console.error('Error pausing/resuming:', e);
      showToast('Erro ao pausar/continuar', 'error');
    }
  };"""
    content = content.replace(toggle_anchor, toggle_replacement)

    # 4. WebSocket handling
    ws_anchor = """      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const merged = data.final_transcript?.segments;
          if (Array.isArray(merged)) {
            setRealtimeSegments(merged);
          }
        } catch (e) {}
      };"""
      
    ws_replacement = """      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'popup') {
            (window as any).electronAPI?.showOverlayPopup?.({ title: data.title, message: data.message, action: data.action });
            return;
          }
          if (data.final_transcript) {
            const merged = data.final_transcript?.segments;
            if (Array.isArray(merged) && isRecordingRef.current) {
              setRealtimeSegments(merged);
            }
          }
        } catch (e) {}
      };"""
    content = content.replace(ws_anchor, ws_replacement)

    # 5. Dashboard props
    dash_anchor = """          <Dashboard
            isRecording={isRecording}
            timer={timer}
            status={status}
            onToggle={handleToggleRecording}
            micEnabled={settings.mic_enabled}
            sysEnabled={settings.system_enabled}
            realtimeSegments={realtimeSegments}
            wsConnected={wsConnected}
          />"""
          
    dash_replacement = """          <Dashboard
            isRecording={isRecording}
            isPaused={isPaused}
            timer={timer}
            status={status}
            onToggle={handleToggleRecording}
            onPauseResume={performPauseResume}
            micEnabled={settings.mic_enabled}
            sysEnabled={settings.system_enabled}
            realtimeSegments={realtimeSegments}
            wsConnected={wsConnected}
          />"""
    content = content.replace(dash_anchor, dash_replacement)

    # 6. Phase 3 Label logic and bulk actions
    action_anchor = """    setSelectedMeeting(m);
    setTab('transcription');
  };

  const deleteMeeting = (id: string) => {
    setMeetings((prev) => prev.filter((m) => m.id !== id));
  };"""
  
    action_replacement = """    setSelectedMeeting(m);
    setTab('transcription');
  };

  const fetchLabels = async () => {
    try {
      const res = await fetch(`${API_URL}/labels`);
      if (res.ok) setLabels(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLabels();
  }, []);

  const handleAddLabel = async (name: string, color: string) => {
    try {
      await fetch(`${API_URL}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: `label_${Date.now()}`, name, color }),
      });
      fetchLabels();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemoveLabel = async (id: string) => {
    try {
      await fetch(`${API_URL}/labels/${id}`, { method: 'DELETE' });
      fetchLabels();
    } catch (e) {
      console.error(e);
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const clearSelection = () => setSelectedIds([]);

  const handleBulkArchive = async (ids: string[]) => {
    try {
      const res = await fetch(`${API_URL}/meetings/bulk-archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        showToast(`${ids.length} transcrições arquivadas`, 'success');
        clearSelection();
        fetchMeetings();
      }
    } catch (e) {
      console.error(e);
      showToast('Erro ao arquivar', 'error');
    }
  };

  const handleBulkDelete = async (ids: string[]) => {
    if (!window.confirm(`Tem certeza que deseja excluir ${ids.length} transcrição(ões)?`)) return;
    try {
      const res = await fetch(`${API_URL}/meetings/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        showToast(`${ids.length} transcrições excluídas`, 'success');
        clearSelection();
        fetchMeetings();
      }
    } catch (e) {
      console.error(e);
      showToast('Erro ao excluir', 'error');
    }
  };

  const deleteMeeting = (id: string) => {
    handleBulkDelete([id]);
  };"""
    content = content.replace(action_anchor, action_replacement)
    
    # 7. Sidebar Calendar Add
    sidebar_anchor = """          <SidebarItem
            label="Settings"
            icon="⚙"
            active={tab === 'settings'}
            onClick={() => setTab('settings')}
          />"""
          
    sidebar_replacement = """          <SidebarItem
            label="Calendar"
            icon="📅"
            active={tab === 'calendar'}
            onClick={() => setTab('calendar')}
          />
          <SidebarItem
            label="Settings"
            icon="⚙"
            active={tab === 'settings'}
            onClick={() => setTab('settings')}
          />"""
    content = content.replace(sidebar_anchor, sidebar_replacement)

    # 8. Meeting and Settings Props
    meetings_settings_anchor = """        {tab === 'meetings' && (
          <Meetings meetings={meetings} onOpen={openMeeting} onDelete={deleteMeeting} />
        )}
        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={meetingSegments}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
          />
        )}
        {tab === 'settings' && (
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            onSave={handleSave}
            saved={saved}
          />
        )}"""
        
    meetings_settings_replacement = """        {tab === 'meetings' && (
          <Meetings 
            meetings={meetings} 
            onOpen={openMeeting} 
            onDelete={(id) => handleBulkDelete([id])}
            onBulkDelete={handleBulkDelete}
            onBulkArchive={handleBulkArchive}
            labels={labels}
            selectedIds={selectedIds}
            onToggleSelection={toggleSelection}
            onClearSelection={clearSelection}
          />
        )}
        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={meetingSegments}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
          />
        )}
        {tab === 'settings' && (
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            onSave={handleSave}
            saved={saved}
            labels={labels}
            onAddLabel={handleAddLabel}
            onRemoveLabel={handleRemoveLabel}
          />
        )}
        {tab === 'calendar' && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-2xl mb-4">
              📅
            </div>
            <h2 className="text-xl font-bold text-gray-200 mb-2">Integração com Google Calendar</h2>
            <p className="text-sm text-gray-500 max-w-sm mb-6">
              Sincronize sua agenda para iniciar gravações automaticamente e associar reuniões aos eventos correspondentes.
            </p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors cursor-pointer border-none opacity-50 cursor-not-allowed">
              Conectar Conta do Google (Em Breve)
            </button>
          </div>
        )}"""
    content = content.replace(meetings_settings_anchor, meetings_settings_replacement)

    # 9. Toast JSX
    toast_anchor = """      </DarkWindow>
    </div>
  );
}"""

    toast_replacement = """      </DarkWindow>
      
      {toast && (
        <div 
          className="fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 z-50 flex items-center gap-2"
          style={{
            background: toast.type === 'success' ? '#14532d' : '#7f1d1d',
            color: toast.type === 'success' ? '#86efac' : '#fca5a5',
            border: `1px solid ${toast.type === 'success' ? '#166534' : '#991b1b'}`,
            animation: 'slide-up 0.3s ease-out forwards'
          }}
        >
          {toast.type === 'success' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5"/></svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
          )}
          {toast.message}
        </div>
      )}
    </div>
  );
}"""
    content = content.replace(toast_anchor, toast_replacement)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("App.tsx successfully patched with all uncommitted and Phase 3 changes!")

if __name__ == "__main__":
    main()
