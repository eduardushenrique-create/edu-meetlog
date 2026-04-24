import { app, BrowserWindow, globalShortcut, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
let isRecording = false;

function getBackendPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'main.py');
  }
  return path.join(__dirname, '..', 'backend', 'main.py');
}

function getHTMLPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'app.asar', 'dist', 'index.html');
  }
  return path.join(__dirname, '..', 'dist', 'index.html');
}

function startBackend() {
  const backendPath = getBackendPath();
  console.log('Starting backend from:', backendPath);
  
  pythonProcess = spawn('python', [backendPath], {
    stdio: ['ignore', 'pipe', 'pipe'],
    cwd: app.isPackaged ? path.dirname(backendPath) : undefined,
  });

  pythonProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`Backend: ${data}`);
  });

  pythonProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`Backend Error: ${data}`);
  });

  pythonProcess.on('close', (code: number | null) => {
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
  const ret1 = globalShortcut.register('CommandOrControl+Alt+R', () => {
    console.log('Hotkey CTRL+ALT+R pressed - Toggle Recording');
    toggleRecording();
  });

  const ret2 = globalShortcut.register('CommandOrControl+Alt+S', () => {
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
  mainWindow = new BrowserWindow({
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

  const htmlPath = getHTMLPath();
  console.log('Loading HTML from:', htmlPath);

  const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';

  if (isDev) {
    mainWindow.loadURL('http://localhost:5174');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(htmlPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
  registerHotkeys();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  globalShortcut.unregisterAll();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.on('recording-state', (_event, state: boolean) => {
  isRecording = state;
});