@echo off
cd /d "%~dp0"
title FunASRVoiceTyper_Turbo Uninstall
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstaller.ps1"
