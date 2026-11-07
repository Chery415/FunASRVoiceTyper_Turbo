@echo off
cd /d "%~dp0"
title FunASRVoiceTyper Turbo v3.2 (Debug)
if not exist ".venv\Scripts\python.exe" goto err
".venv\Scripts\python.exe" main.py
pause
exit /b 0

:err
echo [Error] Cannot find .venv\Scripts\python.exe
pause
