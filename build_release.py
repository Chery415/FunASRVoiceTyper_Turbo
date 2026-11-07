import os
import sys
import shutil
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ASSETS_DIR = os.path.join(PROJECT_DIR, "package_assets")
DIST_DIR = os.path.join(PROJECT_DIR, "dist", "FunASRVoiceTyper_Turbo")
PYINSTALLER_EXE = os.path.join(PROJECT_DIR, ".venv", "Scripts", "pyinstaller.exe")
SPEC_FILE = os.path.join(PROJECT_DIR, "FunASRVoiceTyper_Turbo.spec")

import time

print("=================================================================")
print("  開始執行 FunASRVoiceTyper_Turbo 自動化建置與發行打包流程")
print("=================================================================")

# 0. 先強制關閉可能佔用檔案的背景程序
subprocess.run("taskkill /F /IM FunASRVoiceTyper_Turbo.exe /T", shell=True, capture_output=True)
subprocess.run("taskkill /F /IM LocalVoiceTyper_SenseVoice.exe /T", shell=True, capture_output=True)
subprocess.run("taskkill /F /IM SpeechPipeline_HybridFast.exe /T", shell=True, capture_output=True)
time.sleep(1)

# 1. 執行 PyInstaller 建置
print("\n[1/4] 正在編譯執行檔與打包依賴庫 (PyInstaller)...")
build_dir = os.path.join(PROJECT_DIR, "build")
if os.path.exists(build_dir):
    shutil.rmtree(build_dir, ignore_errors=True)
python_exe = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")
pkg_script = os.path.join(PROJECT_DIR, "build_package.py")
cmd = [python_exe, pkg_script]
res = subprocess.run(cmd, cwd=PROJECT_DIR)
if res.returncode != 0:
    print(f"[錯誤] PyInstaller 編譯失敗，退出碼: {res.returncode}")
    sys.exit(1)

# 2. 複製安裝與解除安裝腳本
print("\n[2/4] 正在複製安裝與解除安裝精靈檔案...")
assets = [
    "Setup_安裝與開機啟動.bat",
    "installer.ps1",
    "Uninstall_解除安裝.bat",
    "uninstaller.ps1"
]
for item in assets:
    src = os.path.join(PKG_ASSETS_DIR, item)
    dst = os.path.join(DIST_DIR, item)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [OK] 已部署: {item}")
    else:
        print(f"  [WARN] 找不到資產檔: {src}")

# 3. 複製外部設定檔 config.json
print("\n[3/4] 正在部署根目錄 config.json...")
cfg_src = os.path.join(PROJECT_DIR, "config.json")
cfg_dst = os.path.join(DIST_DIR, "config.json")
if os.path.exists(cfg_src):
    shutil.copy2(cfg_src, cfg_dst)
    print("  [OK] config.json 已部署至應用程式根目錄")

# 4. 建立 models 目錄捷徑/軟連結 (方便使用者直觀查看)
print("\n[4/4] 正在建立 models 結構連結...")
models_in_internal = os.path.join(DIST_DIR, "_internal", "models")
models_in_root = os.path.join(DIST_DIR, "models")
if os.path.exists(models_in_internal) and not os.path.exists(models_in_root):
    try:
        subprocess.run(["cmd.exe", "/c", "mklink", "/J", models_in_root, models_in_internal], check=True)
        print("  [OK] models 目錄連結已建立")
    except Exception as e:
        print(f"  [WARN] 建立目錄連結跳過: {e}")

print("\n=================================================================")
print("  打包完成！發行目錄位於:")
print(f"  {DIST_DIR}")
print("=================================================================")
