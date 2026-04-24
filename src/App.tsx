import { useState, useEffect } from 'react';
import './types';

type Tab = 'dashboard' | 'meetings' | 'transcription' | 'settings';

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [status, setStatus] = useState<any>(null);
  const [meetings, setMeetings] = useState<any[]>([]);
  const [transcript, setTranscript] = useState<any>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<string | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await window.electronAPI.getStatus();
      setStatus(data);
      setLoading(false);
    } catch (e) {
      console.error('Failed to fetch status:', e);
    }
  };

  const fetchMeetings = async () => {
    try {
      const data = await window.electronAPI.getMeetings();
      setMeetings(data);
    } catch (e) {
      console.error('Failed to fetch meetings:', e);
    }
  };

  const fetchTranscript = async (meetingId: string) => {
    try {
      const data = await window.electronAPI.getTranscript(meetingId);
      setTranscript(data);
    } catch (e) {
      console.error('Failed to fetch transcript:', e);
    }
  };

  const fetchSettings = async () => {
    try {
      const data = await window.electronAPI.getSettings();
      setSettings(data);
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
  };

  const startRecording = async () => {
    try {
      await window.electronAPI.startRecording();
      fetchStatus();
    } catch (e) {
      console.error('Failed to start recording:', e);
    }
  };

  const stopRecording = async () => {
    try {
      await window.electronAPI.stopRecording();
      fetchStatus();
    } catch (e) {
      console.error('Failed to stop recording:', e);
    }
  };

  const saveSettings = async () => {
    try {
      await window.electronAPI.updateSettings(settings);
      alert('Configurações salvas!');
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  };

  useEffect(() => {
    if (tab === 'meetings') fetchMeetings();
    if (tab === 'settings') fetchSettings();
  }, [tab]);

  useEffect(() => {
    if (selectedMeeting) fetchTranscript(selectedMeeting);
  }, [selectedMeeting]);

  const isRecording = status?.state === 'RECORDING';

  return (
    <div className="flex h-screen bg-black text-white font-sans">
      <div className="w-56 p-4 border-r border-gray-800 flex flex-col">
        <h1 className="text-xl font-bold mb-6">Edu MeetLog</h1>
        <nav className="space-y-2 flex-1">
          <button
            onClick={() => { setTab('dashboard'); setSelectedMeeting(null); }}
            className={`w-full text-left px-4 py-2 rounded transition ${
              tab === 'dashboard' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => { setTab('meetings'); setSelectedMeeting(null); }}
            className={`w-full text-left px-4 py-2 rounded transition ${
              tab === 'meetings' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Meetings
          </button>
          <button
            onClick={() => { setTab('transcription'); }}
            className={`w-full text-left px-4 py-2 rounded transition ${
              tab === 'transcription' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Transcription
          </button>
          <button
            onClick={() => { setTab('settings'); }}
            className={`w-full text-left px-4 py-2 rounded transition ${
              tab === 'settings' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Settings
          </button>
        </nav>
      </div>

      <div className="flex-1 p-6 overflow-auto">
        {tab === 'dashboard' && (
          <div className="space-y-6">
            <div>
              <div className="text-gray-400 text-sm mb-1">STATUS</div>
              <div className={`text-2xl ${isRecording ? 'text-red-500' : 'text-green-500'}`}>
                {loading ? 'Loading...' : isRecording ? 'RECORDING' : 'STOPPED'}
              </div>
            </div>
            
            <div>
              <div className="text-gray-400 text-sm mb-1">TEMPO</div>
              <div className="text-4xl font-mono">
                {formatTime(status?.recording_duration || 0)}
              </div>
            </div>

            <button
              onClick={() => isRecording ? stopRecording() : startRecording()}
              className={`px-8 py-4 rounded-lg text-lg font-semibold transition ${
                isRecording 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isRecording ? 'PARAR' : 'INICIAR'}
            </button>

            <div>
              <div className="text-gray-400 text-sm mb-2">FILA</div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-900 p-3 rounded">
                  <div className="text-2xl font-bold">{status?.queue_stats?.pending || 0}</div>
                  <div className="text-sm text-gray-400">Pendentes</div>
                </div>
                <div className="bg-gray-900 p-3 rounded">
                  <div className="text-2xl font-bold">{status?.queue_stats?.processing || 0}</div>
                  <div className="text-sm text-gray-400">Processando</div>
                </div>
                <div className="bg-gray-900 p-3 rounded">
                  <div className="text-2xl font-bold">{status?.queue_stats?.done || 0}</div>
                  <div className="text-sm text-gray-400">Concluídos</div>
                </div>
                <div className="bg-gray-900 p-3 rounded">
                  <div className="text-2xl font-bold">{status?.queue_stats?.failed || 0}</div>
                  <div className="text-sm text-gray-400">Falhas</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {tab === 'meetings' && (
          <div>
            <h2 className="text-2xl mb-4">MEETINGS</h2>
            {meetings.length === 0 ? (
              <p className="text-gray-400">Nenhuma reunião encontrada.</p>
            ) : (
              <div className="space-y-3">
                {meetings.map((meeting: any) => (
                  <div
                    key={meeting.id}
                    onClick={() => { setSelectedMeeting(meeting.id); setTab('transcription'); }}
                    className="p-4 border border-gray-800 rounded-lg cursor-pointer hover:bg-gray-900 transition"
                  >
                    <div className="font-semibold">{meeting.date}</div>
                    <div className="text-sm text-gray-400">
                      Status: {meeting.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'transcription' && (
          <div>
            <h2 className="text-2xl mb-4">TRANSCRIPTION</h2>
            {!selectedMeeting ? (
              <p className="text-gray-400">Selecione uma reunião na aba Meetings.</p>
            ) : !transcript ? (
              <p className="text-gray-400">Carregando...</p>
            ) : (
              <div className="space-y-2 font-mono">
                {transcript.segments?.map((seg: any) => (
                  <div key={seg.id} className="leading-relaxed">
                    <span className="text-gray-500">
                      [{Math.floor(seg.start / 60).toString().padStart(2, '0')}:{Math.floor(seg.start % 60).toString().padStart(2, '0')}]
                    </span>{' '}
                    <span className={seg.speaker === 'user' ? 'text-green-400' : 'text-blue-400'}>
                      {seg.speaker.toUpperCase()}:
                    </span>{' '}
                    {seg.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'settings' && (
          <div>
            <h2 className="text-2xl mb-4">SETTINGS</h2>
            {settings && (
              <div className="space-y-6">
                <div>
                  <div className="text-gray-400 text-sm mb-2">CAPTURA DE ÁUDIO</div>
                  <div className="space-y-3">
                    <label className="flex items-center justify-between bg-gray-900 p-3 rounded">
                      <span>Microfone</span>
                      <input
                        type="checkbox"
                        checked={settings.mic_enabled}
                        onChange={(e) => setSettings({ ...settings, mic_enabled: e.target.checked })}
                        className="w-5 h-5"
                      />
                    </label>
                    <label className="flex items-center justify-between bg-gray-900 p-3 rounded">
                      <span>Sistema (Loopback)</span>
                      <input
                        type="checkbox"
                        checked={settings.system_enabled}
                        onChange={(e) => setSettings({ ...settings, system_enabled: e.target.checked })}
                        className="w-5 h-5"
                      />
                    </label>
                  </div>
                </div>

                <div>
                  <div className="text-gray-400 text-sm mb-2">TRANSCRIÇÃO</div>
                  <div className="space-y-3">
                    <label className="flex items-center justify-between bg-gray-900 p-3 rounded">
                      <span>Modelo</span>
                      <select
                        value={settings.model}
                        onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                        className="bg-gray-800 px-3 py-1 rounded"
                      >
                        <option value="tiny">tiny</option>
                        <option value="base">base</option>
                        <option value="small">small</option>
                        <option value="medium">medium</option>
                        <option value="large-v2">large-v2</option>
                        <option value="large-v3">large-v3</option>
                      </select>
                    </label>
                    <label className="flex items-center justify-between bg-gray-900 p-3 rounded">
                      <span>Workers</span>
                      <input
                        type="number"
                        value={settings.workers}
                        onChange={(e) => setSettings({ ...settings, workers: parseInt(e.target.value) })}
                        className="bg-gray-800 px-3 py-1 rounded w-20 text-center"
                        min={1}
                        max={8}
                      />
                    </label>
                  </div>
                </div>

                <div>
                  <div className="text-gray-400 text-sm mb-2">INICIALIZAÇÃO</div>
                  <label className="flex items-center justify-between bg-gray-900 p-3 rounded">
                    <span>Auto-start ao iniciar app</span>
                    <input
                      type="checkbox"
                      checked={settings.auto_start}
                      onChange={(e) => setSettings({ ...settings, auto_start: e.target.checked })}
                      className="w-5 h-5"
                    />
                  </label>
                </div>

                <button
                  onClick={saveSettings}
                  className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition"
                >
                  SALVAR
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}