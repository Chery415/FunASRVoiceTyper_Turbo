import time
import ctypes
import pyperclip

class TextInjector:
    """
    Windows 原生零延遲文字注入器：
    - 使用 Windows 原生 user32.keybd_event 模擬 Ctrl+V。
    - 快速寫入剪貼簿 -> 原生貼上 -> 延遲 100ms 復原原內容。
    """
    def __init__(self, restore_delay: float = 0.1):
        self.restore_delay = restore_delay

    def fast_paste(self):
        # 0x11 = VK_CONTROL, 0x56 = 'V'
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)

    def inject_text(self, text: str):
        if not text:
            return

        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        try:
            pyperclip.copy(text)
            time.sleep(0.015)
            self.fast_paste()
        finally:
            time.sleep(self.restore_delay)
            try:
                if old_clipboard:
                    pyperclip.copy(old_clipboard)
            except Exception:
                pass
