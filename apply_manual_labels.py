import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to add a <select> or similar to manually add labels in Transcription.
    # Where? Next to the suggestions or in the meeting.labels display.
    
    anchor = """      {meeting?.labels && meeting.labels.length > 0 && (
        <div className="flex gap-2 mb-3">
          {meeting.labels.map(lblId => {"""
          
    # We will modify the header area where labels are displayed.
    # Let's replace the whole block of displaying labels and suggestions.
    
    # Let's add a `handleManualAddLabel` function.
    anchor_func = """  const handleRejectSuggestion = (labelId: string) => {
    setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
  };"""
  
    replacement_func = """  const handleRejectSuggestion = (labelId: string) => {
    setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
  };

  const handleManualAddLabel = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const labelId = e.target.value;
    if (!labelId || !meeting) return;
    const current = meeting.labels || [];
    if (current.includes(labelId)) {
      e.target.value = "";
      return;
    }
    const updated = [...current, labelId];
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      meeting.labels = updated; 
      onLabelsUpdated?.();
      e.target.value = "";
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRemoveLabel = async (labelId: string) => {
    if (!meeting) return;
    const current = meeting.labels || [];
    const updated = current.filter(id => id !== labelId);
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      meeting.labels = updated; 
      onLabelsUpdated?.();
    } catch (err) {
      console.error(err);
    }
  };"""
    
    if anchor_func in content:
        content = content.replace(anchor_func, replacement_func)

    anchor_ui = """      {meeting?.labels && meeting.labels.length > 0 && (
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
      )}"""
      
    replacement_ui = """      <div className="flex gap-2 mb-3 items-center flex-wrap">
        {meeting?.labels?.map(lblId => {
          const lbl = labels?.find(l => l.id === lblId);
          if (!lbl) return null;
          return (
            <span key={lblId} className="flex items-center text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: lbl.color + '20', color: lbl.color, border: `1px solid ${lbl.color}40` }}>
              {lbl.name}
              <button onClick={() => handleRemoveLabel(lblId)} className="ml-1 text-current opacity-60 hover:opacity-100 bg-transparent border-none cursor-pointer p-0 font-bold">&times;</button>
            </span>
          );
        })}
        <select
          onChange={handleManualAddLabel}
          defaultValue=""
          className="bg-transparent border border-gray-700 text-gray-400 rounded px-1 py-0.5 text-[10px] outline-none cursor-pointer hover:border-gray-500 transition-colors"
        >
          <option value="" disabled>+ Adicionar Rótulo</option>
          {(labels || []).filter(l => !(meeting?.labels || []).includes(l.id)).map(l => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
      </div>"""
      
    if anchor_ui in content:
        content = content.replace(anchor_ui, replacement_ui)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("F3.3.7 - Manual label selector added to Transcription")

if __name__ == "__main__":
    main()
