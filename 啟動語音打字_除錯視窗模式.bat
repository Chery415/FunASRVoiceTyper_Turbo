@echo off
cd /d "%~dp0"
title FunASRVoiceTyper Turbo v3.2 (Debug Console)
if not exist ".venv\Scripts\python.exe" goto err
echo Starting FunASRVoiceTyper Turbo in console mode...
".venv\Scripts\python.exe" main.py
pause
exit /b 0

:err
echo [Error] Cannot find .venv\Scripts\python.exe
pause
