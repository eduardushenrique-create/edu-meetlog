import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Transcription Signature
    transcription_sig_anchor = """function Transcription({
  meeting,
  segments,
  onBack,
}: {
  meeting: Meeting | null;
  segments: Segment[];
  onBack: () => void;
}) {"""
    transcription_sig_replacement = """function Transcription({
  meeting,
  segments,
  labels,
  onBack,
  onLabelsUpdated
}: {
  meeting: Meeting | null;
  segments: Segment[];
  labels?: any[];
  onBack: () => void;
  onLabelsUpdated?: () => void;
}) {
  const [suggestedLabels, setSuggestedLabels] = useState<any[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const handleSuggest = async () => {
    if (!meeting) return;
    setIsSuggesting(true);
    try {
      const res = await fetch(`${API_URL}/meetings/${meeting.id}/suggest-labels`, { method: 'POST' });
      const data = await res.json();
      if (data.suggested_label_ids) {
        const found = (labels || []).filter(l => data.suggested_label_ids.includes(l.id));
        const newSuggestions = found.filter(l => !(meeting.labels || []).includes(l.id));
        setSuggestedLabels(newSuggestions);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleAcceptSuggestion = async (labelId: string) => {
    if (!meeting) return;
    const current = meeting.labels || [];
    const updated = [...current, labelId];
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
      meeting.labels = updated; 
      onLabelsUpdated?.();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRejectSuggestion = (labelId: string) => {
    setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
  };"""

    if transcription_sig_anchor in content:
        content = content.replace(transcription_sig_anchor, transcription_sig_replacement)

    # 2. Add Suggest Button
    suggest_btn_anchor = """          <div className="flex gap-1.5">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs rounded-md cursor-pointer font-sans transition-all border\""""
              
    suggest_btn_replacement = """          <div className="flex gap-1.5">
            <button
              onClick={handleSuggest}
              disabled={isSuggesting}
              className="px-3 py-1.5 text-xs rounded-md cursor-pointer font-sans transition-all border bg-purple-900/30 border-purple-800 text-purple-300 hover:bg-purple-800/50 flex items-center gap-1.5"
            >
              {isSuggesting ? '⏳ Pensando...' : '🪄 Sugerir Rótulos'}
            </button>
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs rounded-md cursor-pointer font-sans transition-all border\""""
              
    if suggest_btn_anchor in content:
        content = content.replace(suggest_btn_anchor, suggest_btn_replacement)

    # 3. Add Suggestions Box and Labels to UI
    suggestions_box_anchor = """        </div>
      </div>

      <div className="flex gap-3 mb-3">"""
      
    suggestions_box_replacement = """        </div>
      </div>

      {meeting?.labels && meeting.labels.length > 0 && (
        <div className="flex gap-2 mb-3">
          {meeting.labels.map(lblId => {
            const lbl = labels?.find(l => l.id === lblId);
            if (!lbl) return null;
            return (
              <span key={lblId} className="text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: lbl.color + '20', color: lbl.color, border: `1px solid ${lbl.color}40` }}>
                {lbl.name}
              </span>
            );
          })}
        </div>
      )}

      {suggestedLabels.length > 0 && (
        <div className="mb-4 p-3 bg-purple-900/10 border border-purple-900/50 rounded-md">
          <div className="text-xs font-semibold text-purple-300 mb-2">Sugestões da IA:</div>
          <div className="flex flex-wrap gap-2">
            {suggestedLabels.map(l => (
              <div key={l.id} className="flex items-center gap-2 px-2 py-1 rounded text-xs font-medium bg-gray-900 border border-gray-800 text-gray-200">
                <span className="w-2 h-2 rounded-full" style={{ background: l.color }} />
                {l.name}
                <div className="flex items-center ml-1 gap-2 border-l border-gray-700 pl-2">
                  <button onClick={() => handleAcceptSuggestion(l.id)} className="bg-transparent border-none text-green-500 hover:text-green-400 cursor-pointer p-0 font-bold" title="Aceitar">✓</button>
                  <button onClick={() => handleRejectSuggestion(l.id)} className="bg-transparent border-none text-red-500 hover:text-red-400 cursor-pointer p-0 font-bold" title="Recusar">✕</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3 mb-3">"""
    
    if suggestions_box_anchor in content:
        content = content.replace(suggestions_box_anchor, suggestions_box_replacement)

    # 4. Update App JSX for Transcription
    app_jsx_anchor = """        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={meetingSegments}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
          />
        )}"""
        
    app_jsx_replacement = """        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={meetingSegments}
            labels={labels}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
            onLabelsUpdated={fetchMeetings}
          />
        )}"""
        
    if app_jsx_anchor in content:
        content = content.replace(app_jsx_anchor, app_jsx_replacement)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("AI suggestions UI successfully added to App.tsx")

if __name__ == "__main__":
    main()
