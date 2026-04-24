import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  startRecording: () => ipcRenderer.invoke('recording:start'),
  stopRecording: () => ipcRenderer.invoke('recording:stop'),
  getStatus: () => ipcRenderer.invoke('status:get'),
  onStatusChange: (callback: (status: string) => void) => {
    ipcRenderer.on('status:changed', (_event, status) => callback(status));
  },
});