@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\guthub\ollama\start-ollama.ps1"
if errorlevel 1 goto failed
cd /d "%~dp0"
"%~dp0..\..\.venv\Scripts\python.exe" -m tui.app
if errorlevel 1 goto failed
exit /b 0
:failed
echo Agent could not start. Check the error above.
pause
exit /b 1
