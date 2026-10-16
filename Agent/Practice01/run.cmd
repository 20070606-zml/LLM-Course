@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PYTHON%" goto bundled
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto launcher
python "%~dp0chat.py"
exit /b %errorlevel%

:bundled
"%BUNDLED_PYTHON%" "%~dp0chat.py"
exit /b %errorlevel%

:launcher
py -3 "%~dp0chat.py"
exit /b %errorlevel%
