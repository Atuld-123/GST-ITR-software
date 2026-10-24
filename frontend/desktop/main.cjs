const { app, BrowserWindow, dialog } = require("electron");
const path = require("path");

const startUrl = process.env.TAXSPHERE_DESKTOP_URL || "http://127.0.0.1:3000";

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1120,
    minHeight: 720,
    title: "TaxSphere India",
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  window.removeMenu();
  window.loadURL(startUrl).catch(() => dialog.showErrorBox("TaxSphere server unavailable", "Start the TaxSphere application service, then reopen this desktop application."));
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
