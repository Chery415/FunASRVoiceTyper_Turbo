@echo off
setlocal
cd /d "%~dp0"
echo Starting FunASRVoiceTyper_Turbo v3.3 (Lean Golden Edition)...
if exist "FunASRVoiceTyper_Turbo.exe" (
    start "" "FunASRVoiceTyper_Turbo.exe"
    exit /b 0
)
if exist "dist\FunASRVoiceTyper_Turbo\FunASRVoiceTyper_Turbo.exe" (
    cd /d "%~dp0dist\FunASRVoiceTyper_Turbo"
    start "" "FunASRVoiceTyper_Turbo.exe"
    exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
    exit /b 0
)
echo [ERROR] Executable or virtual environment not found.
pause
