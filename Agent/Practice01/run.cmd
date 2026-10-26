@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%~dp0..\..\.venv\Scripts\python.exe" goto venv
if exist "%BUNDLED_PYTHON%" goto bundled
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto launcher
python "%~dp0chat.py"
goto finished
:venv
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0chat.py"
goto finished
:bundled
"%BUNDLED_PYTHON%" "%~dp0chat.py"
goto finished
:launcher
py -3 "%~dp0chat.py"
:finished
set "CHAT_EXIT=%errorlevel%"
if "%CHAT_EXIT%"=="0" exit /b 0
echo.
echo Chat could not start. Check the error above.
echo Model configuration: %~dp0config.ini
pause
exit /b %CHAT_EXIT%
