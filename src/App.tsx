import { useState } from 'react';

type Tab = 'dashboard' | 'meetings' | 'transcription' | 'settings';

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [recording, setRecording] = useState(false);

  return (
    <div className="flex h-screen bg-black text-white">
      <div className="w-56 p-4 border-r border-gray-800">
        <h1 className="text-xl font-bold mb-6">Edu MeetLog</h1>
        <nav className="space-y-2">
          <button
            onClick={() => setTab('dashboard')}
            className={`w-full text-left px-4 py-2 rounded ${
              tab === 'dashboard' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setTab('meetings')}
            className={`w-full text-left px-4 py-2 rounded ${
              tab === 'meetings' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Meetings
          </button>
          <button
            onClick={() => setTab('transcription')}
            className={`w-full text-left px-4 py-2 rounded ${
              tab === 'transcription' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Transcription
          </button>
          <button
            onClick={() => setTab('settings')}
            className={`w-full text-left px-4 py-2 rounded ${
              tab === 'settings' ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            Settings
          </button>
        </nav>
      </div>

      <div className="flex-1 p-6">
        {tab === 'dashboard' && (
          <>
            <div className="text-2xl mb-4">
              STATUS: {recording ? 'Recording' : 'Stopped'}
            </div>
            <button
              onClick={() => setRecording(!recording)}
              className="px-6 py-3 bg-blue-600 rounded hover:bg-blue-700"
            >
              {recording ? 'Stop' : 'Start'}
            </button>
          </>
        )}
        {tab === 'meetings' && (
          <div>
            <h2 className="text-2xl mb-4">MEETINGS</h2>
            <p className="text-gray-400">Nenhuma reunião encontrada.</p>
          </div>
        )}
        {tab === 'transcription' && (
          <div>
            <h2 className="text-2xl mb-4">TRANSCRIPTION</h2>
            <p className="text-gray-400">Selecione uma reunião para visualizar.</p>
          </div>
        )}
        {tab === 'settings' && (
          <div>
            <h2 className="text-2xl mb-4">SETTINGS</h2>
            <p className="text-gray-400">Configurações em desenvolvimento.</p>
          </div>
        )}
      </div>
    </div>
  );
}