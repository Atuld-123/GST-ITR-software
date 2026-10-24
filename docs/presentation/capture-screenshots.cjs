const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const path = require("path");

const pages = process.argv[2] ? [process.argv[2]] : ["", "login", "onboarding", "clients", "gst", "accounting", "reconciliation"];
const output = path.resolve(__dirname, "screenshots");

app.whenReady().then(async () => {
  fs.mkdirSync(output, { recursive: true });
  const window = new BrowserWindow({ width: 1440, height: 920, show: false, webPreferences: { sandbox: true } });
  for (const page of pages) {
    await window.loadURL(`http://127.0.0.1:3000/${page}`);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const image = await window.capturePage();
    fs.writeFileSync(path.join(output, `${page || "dashboard"}.png`), image.toPNG());
  }
  app.quit();
});
