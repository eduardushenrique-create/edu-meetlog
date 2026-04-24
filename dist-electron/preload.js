"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    startRecording: () => electron_1.ipcRenderer.invoke('recording:start'),
    stopRecording: () => electron_1.ipcRenderer.invoke('recording:stop'),
    getStatus: () => electron_1.ipcRenderer.invoke('status:get'),
    onStatusChange: (callback) => {
        electron_1.ipcRenderer.on('status:changed', (_event, status) => callback(status));
    },
});
