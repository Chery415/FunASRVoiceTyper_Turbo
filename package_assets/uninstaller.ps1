$ErrorActionPreference = 'SilentlyContinue'

Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "  FunASRVoiceTyper_Turbo - 解除安裝精靈" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow

$appName = "FunASRVoiceTyper_Turbo"
$installDir = "$env:LOCALAPPDATA\Programs\$appName"

# 1. 關閉程序
cmd.exe /c "taskkill /F /IM FunASRVoiceTyper_Turbo.exe /T >nul 2>&1"
cmd.exe /c "taskkill /F /IM LocalVoiceTyper_SenseVoice.exe /T >nul 2>&1"
cmd.exe /c "taskkill /F /IM SpeechPipeline_HybridFast.exe /T >nul 2>&1"
Stop-Process -Name $appName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. 移除開機註冊表
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name $appName -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "LocalVoiceTyper_SenseVoice" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "SpeechPipeline_HybridFast" -ErrorAction SilentlyContinue
Write-Host "[[OK]] 開機常駐啟動已自註冊表中移除" -ForegroundColor Gray

# 3. 移除捷徑
$desktopDir = [Environment]::GetFolderPath("Desktop")
Remove-Item "$desktopDir\FunASRVoiceTyper Turbo.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$desktopDir\LocalVoiceTyper SenseVoice.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$desktopDir\SpeechPipeline HybridFast.lnk" -Force -ErrorAction SilentlyContinue
$startMenuPrograms = [Environment]::GetFolderPath("Programs")
Remove-Item "$startMenuPrograms\FunASRVoiceTyper Turbo.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$startMenuPrograms\LocalVoiceTyper SenseVoice.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$startMenuPrograms\SpeechPipeline HybridFast.lnk" -Force -ErrorAction SilentlyContinue
Write-Host "[[OK]] 桌面與開始功能表捷徑已刪除" -ForegroundColor Gray

# 4. 刪除安裝資料夾
if (Test-Path $installDir) {
    Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[[OK]] 安裝目錄已清理完畢: $installDir" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[完成] FunASRVoiceTyper_Turbo 已完全解除安裝。" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 2
exit 0
