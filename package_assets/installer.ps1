# PowerShell 安裝與開機啟動註冊邏輯
$ErrorActionPreference = 'Stop'

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  FunASRVoiceTyper_Turbo 語音打字系統 - 安裝精靈" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$sourceDir = $PSScriptRoot
$appName = "FunASRVoiceTyper_Turbo"
$installDir = "$env:LOCALAPPDATA\Programs\$appName"

# 1. 檢查並關閉已在運行的舊程序
Write-Host "[1/5] 檢查並安全關閉舊程序..." -ForegroundColor Yellow
cmd.exe /c "taskkill /F /IM FunASRVoiceTyper_Turbo.exe /T >nul 2>&1"
cmd.exe /c "taskkill /F /IM LocalVoiceTyper_SenseVoice.exe /T >nul 2>&1"
cmd.exe /c "taskkill /F /IM SpeechPipeline_HybridFast.exe /T >nul 2>&1"
Start-Sleep -Seconds 1

# 2. 建立目標資料夾並複製檔案
Write-Host "[2/5] 正在安裝程式至: $installDir ..." -ForegroundColor Green
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$robocopyArgs = @(
    $sourceDir,
    $installDir,
    "/E",
    "/PURGE",
    "/R:2",
    "/W:1",
    "/XD", ".git", "__pycache__",
    "/XF", "Setup_安裝與開機啟動.bat", "installer.ps1"
)
& robocopy.exe @robocopyArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    Write-Host "[錯誤] 檔案複製失敗，錯誤碼: $LASTEXITCODE" -ForegroundColor Red
    pause
    exit 1
}

$exePath = "$installDir\$appName.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "[錯誤] 安裝檔案驗證失敗，找不到 $exePath" -ForegroundColor Red
    pause
    exit 1
}

# 3. 註冊 Windows 開機自動常駐啟動 (HKCU Run)
Write-Host "[3/5] 正在設定 Windows 開機直接常駐啟動..." -ForegroundColor Green
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$regValue = "`"$exePath`""
Set-ItemProperty -Path $regPath -Name $appName -Value $regValue -Force
Write-Host "      [OK] 註冊表開機啟動已配置: $regValue" -ForegroundColor Gray

# 4. 建立桌面與開始功能表捷徑
Write-Host "[4/5] 正在建立桌面與開始功能表捷徑..." -ForegroundColor Green
$wshell = New-Object -ComObject WScript.Shell

$desktopDir = [Environment]::GetFolderPath("Desktop")
$desktopShortcutPath = "$desktopDir\FunASRVoiceTyper Turbo.lnk"
$shortcut = $wshell.CreateShortcut($desktopShortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "FunASRVoiceTyper Turbo 雙引擎極速語音打字系統"
$shortcut.Save()

$startMenuPrograms = [Environment]::GetFolderPath("Programs")
$startMenuShortcutPath = "$startMenuPrograms\FunASRVoiceTyper Turbo.lnk"
$shortcut2 = $wshell.CreateShortcut($startMenuShortcutPath)
$shortcut2.TargetPath = $exePath
$shortcut2.WorkingDirectory = $installDir
$shortcut2.Description = "FunASRVoiceTyper Turbo 雙引擎極速語音打字系統"
$shortcut2.Save()

Write-Host "      [OK] 桌面與開始功能表捷徑已建立完成" -ForegroundColor Gray

# 5. 立即啟動常駐
Write-Host "[5/5] 正在為您啟動程式常駐於系統匣..." -ForegroundColor Green
try {
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = "`"$exePath`""} | Out-Null
} catch {
    cmd.exe /c start "" "$exePath"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  [*] 安裝成功！" -ForegroundColor Green
Write-Host "  1. 程式已在背景常駐，請查看螢幕右下角工作列系統匣。" -ForegroundColor White
Write-Host "  2. 開機常駐啟動功能已啟用，未來開機自動執行，無須手動點擊！" -ForegroundColor White
Write-Host "  3. 隨時可在任何軟體中，按一下 [右側 Ctrl] 提示音開始說話，說完再按一下 [右側 Ctrl] 即刻完成打字。" -ForegroundColor Cyan
Write-Host "  4. 支援右鍵系統匣即時切換 SenseVoice-Small 與 Paraformer-large 雙模型！" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 3
exit 0
