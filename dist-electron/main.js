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
let popupWindow = null;
let pythonProcess = null;
let isRecording = false;
function getBackendPath() {
    if (electron_1.app.isPackaged) {
        return path.join(process.resourcesPath, 'backend', 'main.py');
    }
    return path.join(__dirname, '..', 'backend', 'main.py');
}
function getPythonCommand() {
    if (electron_1.app.isPackaged) {
        return path.join(process.resourcesPath, 'backend', 'venv', 'Scripts', 'python.exe');
    }
    return 'python';
}
function getHTMLPath() {
    if (electron_1.app.isPackaged) {
        return path.join(process.resourcesPath, 'app.asar', 'dist', 'index.html');
    }
    return path.join(__dirname, '..', 'dist', 'index.html');
}
function startBackend() {
    const backendPath = getBackendPath();
    const pythonCommand = getPythonCommand();
    console.log('Starting backend from:', backendPath);
    console.log('Using Python command:', pythonCommand);
    pythonProcess = (0, child_process_1.spawn)(pythonCommand, [backendPath], {
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: electron_1.app.isPackaged ? path.dirname(backendPath) : undefined,
    });
    pythonProcess.on('error', (error) => {
        console.error('Backend spawn failed:', error);
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
function closeApp() {
    if (mainWindow) {
        mainWindow.close();
    }
}
function minimizeApp() {
    if (mainWindow) {
        mainWindow.minimize();
    }
}
function maximizeApp() {
    if (mainWindow) {
        if (mainWindow.isMaximized()) {
            mainWindow.unmaximize();
        }
        else {
            mainWindow.maximize();
        }
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
    const ret3 = electron_1.globalShortcut.register('CommandOrControl+F12', () => {
        console.log('Hotkey CTRL+F12 pressed - Toggle Recording');
        toggleRecording();
    });
    if (!ret1)
        console.error('Failed to register CTRL+ALT+R');
    if (!ret2)
        console.error('Failed to register CTRL+ALT+S');
    if (!ret3)
        console.error('Failed to register CTRL+F12');
}
function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
        width: 860,
        height: 560,
        minWidth: 800,
        minHeight: 520,
        frame: false,
        transparent: true,
        resizable: true,
        thickFrame: true,
        autoHideMenuBar: true,
        backgroundColor: '#00000000',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    mainWindow.setResizable(true);
    mainWindow.setMinimumSize(800, 520);
    electron_1.ipcMain.on('window-minimize', minimizeApp);
    electron_1.ipcMain.on('window-maximize', maximizeApp);
    electron_1.ipcMain.on('window-close', closeApp);
    electron_1.ipcMain.handle('select-output-folder', async () => {
        const { dialog } = require('electron');
        const result = await dialog.showOpenDialog(mainWindow, {
            properties: ['openDirectory']
        });
        return result.canceled ? null : result.filePaths[0];
    });
    const htmlPath = getHTMLPath();
    console.log('Loading HTML from:', htmlPath);
    const isDev = !electron_1.app.isPackaged || process.env.NODE_ENV === 'development';
    if (isDev) {
        mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html')).then(() => {
            console.log('Loaded local dist/index.html');
        }).catch((e) => {
            console.error('Failed to load local HTML:', e);
            mainWindow?.loadURL('http://localhost:5174').catch(console.error);
        });
    }
    else {
        mainWindow.loadFile(htmlPath);
    }
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
function createPopupWindow(title, message, action = 'start') {
    if (popupWindow) {
        popupWindow.close();
    }
    const { screen } = require('electron');
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width } = primaryDisplay.workAreaSize;
    popupWindow = new electron_1.BrowserWindow({
        width: 320,
        height: 120,
        x: width - 340,
        y: 20,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        resizable: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        }
    });
    const htmlPath = getHTMLPath();
    const isDev = !electron_1.app.isPackaged || process.env.NODE_ENV === 'development';
    const queryUrl = `?popup=true&title=${encodeURIComponent(title)}&message=${encodeURIComponent(message)}&action=${encodeURIComponent(action)}`;
    if (isDev) {
        popupWindow.loadURL(`http://localhost:5174${queryUrl}`);
    }
    else {
        popupWindow.loadFile(htmlPath, { search: queryUrl });
    }
    setTimeout(() => {
        if (popupWindow)
            popupWindow.close();
    }, 30000);
}
electron_1.ipcMain.on('show-overlay-popup', (_event, { title, message, action }) => {
    createPopupWindow(title, message, action);
});
electron_1.ipcMain.on('close-overlay-popup', () => {
    if (popupWindow) {
        popupWindow.close();
        popupWindow = null;
    }
});
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
