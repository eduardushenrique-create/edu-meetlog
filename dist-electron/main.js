"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
let mainWindow = null;
let pythonProcess = null;
let isRecording = false;
function startBackend() {
    const backendPath = path.join(__dirname, '..', 'backend', 'main.py');
    pythonProcess = (0, child_process_1.spawn)('python', [backendPath], {
        stdio: ['ignore', 'pipe', 'pipe'],
    });
    pythonProcess.stdout?.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });
    pythonProcess.stderr?.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });
    pythonProcess.on('close', (code) => {
        console.log(`Backend closed with code ${code}`);
    });
}
function toggleRecording() {
    isRecording = !isRecording;
    if (mainWindow) {
        mainWindow.webContents.send('recording-toggle', isRecording);
    }
}
function showApp() {
    if (mainWindow) {
        if (mainWindow.isMinimized()) {
            mainWindow.restore();
        }
        mainWindow.show();
        mainWindow.focus();
    }
}
function registerHotkeys() {
    const ret1 = electron_1.globalShortcut.register('CommandOrControl+Alt+R', () => {
        console.log('Hotkey CTRL+ALT+R pressed - Toggle Recording');
        toggleRecording();
    });
    const ret2 = electron_1.globalShortcut.register('CommandOrControl+Alt+S', () => {
        console.log('Hotkey CTRL+ALT+S pressed - Show App');
        showApp();
    });
    if (!ret1) {
        console.error('Failed to register CTRL+ALT+R');
    }
    if (!ret2) {
        console.error('Failed to register CTRL+ALT+S');
    }
}
function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
        width: 900,
        height: 700,
        minWidth: 800,
        minHeight: 600,
        backgroundColor: '#000',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
    }
    else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
electron_1.app.whenReady().then(() => {
    startBackend();
    createWindow();
    registerHotkeys();
});
electron_1.app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    electron_1.globalShortcut.unregisterAll();
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
electron_1.ipcMain.on('recording-state', (_event, state) => {
    isRecording = state;
});
