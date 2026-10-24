@echo off
setlocal
set "ROOT=%~dp0"

start "TaxSphere API" /min cmd /c "cd /d "%ROOT%backend" && .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000"
start "TaxSphere Frontend" /min cmd /c "cd /d "%ROOT%frontend" && "C:\Program Files\nodejs\npm.cmd" run dev -- --hostname 0.0.0.0 --port 3000"

ping 127.0.0.1 -n 7 >nul
start "" "http://127.0.0.1:3000/login"
