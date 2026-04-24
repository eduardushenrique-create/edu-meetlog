import { contextBridge, ipcRenderer } from 'electron';

const API_URL = 'http://127.0.0.1:8000';

contextBridge.exposeInMainWorld('electronAPI', {
  startRecording: () => fetch(`${API_URL}/recording/start`, { method: 'POST' }).then(r => r.json()),
  stopRecording: () => fetch(`${API_URL}/recording/stop`, { method: 'POST' }).then(r => r.json()),
  getStatus: () => fetch(`${API_URL}/status`).then(r => r.json()),
  getMeetings: () => fetch(`${API_URL}/meetings`).then(r => r.json()),
  getTranscript: (meetingId: string) => fetch(`${API_URL}/transcripts/${meetingId}`).then(r => r.json()),
  getSettings: () => fetch(`${API_URL}/settings`).then(r => r.json()),
  updateSettings: (settings: any) => fetch(`${API_URL}/settings`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  }).then(r => r.json()),
});