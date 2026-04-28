import { contextBridge, ipcRenderer } from 'electron';

const API_URL = 'http://127.0.0.1:8000';

contextBridge.exposeInMainWorld('electronAPI', {
  startRecording: (settings: any) => fetch(`${API_URL}/recording/start`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  }).then(r => r.json()),
  pauseRecording: () => fetch(`${API_URL}/recording/pause`, { method: 'POST' }).then(r => r.json()),
  resumeRecording: () => fetch(`${API_URL}/recording/resume`, { method: 'POST' }).then(r => r.json()),
  finalizeRecording: () => fetch(`${API_URL}/recording/finalize`, { method: 'POST' }).then(r => r.json()),
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
  onRecordingToggle: (callback: (recording: boolean) => void) => {
    ipcRenderer.on('recording-toggle', (_event, recording) => callback(recording));
  },
  minimizeWindow: () => ipcRenderer.send('window-minimize'),
  maximizeWindow: () => ipcRenderer.send('window-maximize'),
  closeWindow: () => ipcRenderer.send('window-close'),
});