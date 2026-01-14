const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { machineIdSync } = require('node-machine-id');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
        title: "Aarambha Softwares - Pharmacy Management System",
        icon: path.join(__dirname, 'assets/icon.png')
    });

    win.loadURL(
        isDev
            ? 'http://localhost:3000'
            : `file://${path.join(__dirname, '../frontend/dist/index.html')}`
    );

    // win.removeMenu(); // Optional: remove menu bar for production
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// IPC handler for Machine ID
ipcMain.handle('get-machine-id', () => {
    return machineIdSync();
});
