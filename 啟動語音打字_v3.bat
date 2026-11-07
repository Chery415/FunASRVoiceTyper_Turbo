@echo off
cd /d "%~dp0"
title FunASRVoiceTyper Turbo v3.2
if not exist ".venv\Scripts\pythonw.exe" goto err
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:err
echo [Error] Cannot find .venv\Scripts\pythonw.exe
pause
