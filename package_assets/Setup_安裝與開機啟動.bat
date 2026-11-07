@echo off
cd /d "%~dp0"
title FunASRVoiceTyper_Turbo Setup
echo Starting setup wizard, please wait...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if errorlevel 1 (
    echo.
    echo [ERROR] Setup encountered an issue. Please review the messages above.
    pause
)
