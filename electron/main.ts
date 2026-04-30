import { app, BrowserWindow, globalShortcut, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let popupWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
let isRecording = false;

function getBackendPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'main.py');
  }
  return path.join(__dirname, '..', 'backend', 'main.py');
}

function getPythonCommand(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'venv', 'Scripts', 'python.exe');
  }
  return 'python';
}

function getHTMLPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'app.asar', 'dist', 'index.html');
  }
  return path.join(__dirname, '..', 'dist', 'index.html');
}

function startBackend() {
  const backendPath = getBackendPath();
  const pythonCommand = getPythonCommand();
  console.log('Starting backend from:', backendPath);
  console.log('Using Python command:', pythonCommand);
  
  pythonProcess = spawn(pythonCommand, [backendPath], {
    stdio: ['ignore', 'pipe', 'pipe'],
    cwd: app.isPackaged ? path.dirname(backendPath) : undefined,
  });

  pythonProcess.on('error', (error: Error) => {
    console.error('Backend spawn failed:', error);
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
    } else {
      mainWindow.maximize();
    }
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

  const ret3 = globalShortcut.register('CommandOrControl+F12', () => {
    console.log('Hotkey CTRL+F12 pressed - Toggle Recording');
    toggleRecording();
  });

  if (!ret1) console.error('Failed to register CTRL+ALT+R');
  if (!ret2) console.error('Failed to register CTRL+ALT+S');
  if (!ret3) console.error('Failed to register CTRL+F12');
}

function createWindow() {
  mainWindow = new BrowserWindow({
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

  ipcMain.on('window-minimize', minimizeApp);
  ipcMain.on('window-maximize', maximizeApp);
  ipcMain.on('window-close', closeApp);
  ipcMain.handle('select-output-folder', async () => {
    const { dialog } = require('electron');
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ['openDirectory']
    });
    return result.canceled ? null : result.filePaths[0];
  });

  const htmlPath = getHTMLPath();
  console.log('Loading HTML from:', htmlPath);

  const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';

  if (isDev) {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html')).then(() => {
      console.log('Loaded local dist/index.html');
    }).catch((e) => {
      console.error('Failed to load local HTML:', e);
      mainWindow?.loadURL('http://localhost:5174').catch(console.error);
    });
  } else {
    mainWindow.loadFile(htmlPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createPopupWindow(title: string, message: string, action: string = 'start') {
  if (popupWindow) {
    popupWindow.close();
  }

  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width } = primaryDisplay.workAreaSize;

  popupWindow = new BrowserWindow({
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
  const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';
  const queryUrl = `?popup=true&title=${encodeURIComponent(title)}&message=${encodeURIComponent(message)}&action=${encodeURIComponent(action)}`;

  if (isDev) {
    popupWindow.loadURL(`http://localhost:5174${queryUrl}`);
  } else {
    popupWindow.loadFile(htmlPath, { search: queryUrl });
  }

  setTimeout(() => {
    if (popupWindow) popupWindow.close();
  }, 30000);
}

ipcMain.on('show-overlay-popup', (_event, { title, message, action }) => {
  createPopupWindow(title, message, action);
});

ipcMain.on('close-overlay-popup', () => {
  if (popupWindow) {
    popupWindow.close();
    popupWindow = null;
  }
});

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
