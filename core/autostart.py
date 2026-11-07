import os
import sys
import winreg

APP_NAME = "FunASRVoiceTyper_Turbo"

def get_executable_path() -> str:
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    else:
        main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        return f'"{sys.executable}" "{main_py}"'

def is_auto_start_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart] 檢查狀態失敗: {e}")
        return False

def set_auto_start(enable: bool) -> bool:
    run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_key_path,
            0,
            winreg.KEY_SET_VALUE
        )
        if enable:
            exe_path = get_executable_path()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            print(f"[Autostart] 已新增開機自啟動: {exe_path}")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                print("[Autostart] 已刪除開機自啟動項目。")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Autostart] 設定開機自啟動失敗: {e}")
        return False
