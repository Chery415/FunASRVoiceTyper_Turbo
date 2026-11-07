import threading
import winsound
from pynput import keyboard

def play_start_tone():
    """錄音開始提示音：1000Hz, 120ms"""
    try:
        winsound.Beep(1000, 120)
    except Exception:
        pass

def play_stop_tone():
    """錄音停止提示音：750Hz, 120ms"""
    try:
        winsound.Beep(750, 120)
    except Exception:
        pass

class ToggleVoiceController:
    def __init__(self, hotkey: str, on_start, on_stop):
        self.hotkey_str = hotkey.strip().lower()
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_recording = False
        self.lock = threading.Lock()
        self.listener = None
        self._key_pressed_set = set()

    def _normalize_key(self, key):
        if isinstance(key, keyboard.Key):
            mapping = {
                keyboard.Key.ctrl_r: "right ctrl",
                keyboard.Key.ctrl_l: "left ctrl",
                keyboard.Key.alt_r: "right alt",
                keyboard.Key.alt_l: "left alt",
                keyboard.Key.shift_r: "right shift",
                keyboard.Key.shift_l: "left shift",
                keyboard.Key.f8: "f8",
                keyboard.Key.f1: "f1",
                keyboard.Key.f2: "f2",
                keyboard.Key.f3: "f3",
                keyboard.Key.f4: "f4",
                keyboard.Key.f5: "f5",
                keyboard.Key.f6: "f6",
                keyboard.Key.f7: "f7",
                keyboard.Key.f9: "f9",
                keyboard.Key.f10: "f10",
                keyboard.Key.f11: "f11",
                keyboard.Key.f12: "f12",
                keyboard.Key.space: "space",
            }
            return mapping.get(key, key.name.lower() if hasattr(key, 'name') else str(key))
        elif hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'vk'):
            if key.vk == 163:
                return "right ctrl"
            elif key.vk == 162:
                return "left ctrl"
            elif key.vk == 165:
                return "right alt"
            elif key.vk == 164:
                return "left alt"
            elif key.vk == 119:
                return "f8"
        return str(key).lower()

    def _on_press(self, key):
        norm_key = self._normalize_key(key)
        if norm_key in self._key_pressed_set:
            return
        self._key_pressed_set.add(norm_key)

        is_triggered = False
        target = self.hotkey_str

        if target in ("right ctrl", "rctrl", "right control"):
            if norm_key == "right ctrl":
                is_triggered = True
        elif target in ("right alt", "ralt", "right menu"):
            if norm_key == "right alt":
                is_triggered = True
        elif target in ("left ctrl", "lctrl"):
            if norm_key == "left ctrl":
                is_triggered = True
        elif target == "f8":
            if norm_key == "f8":
                is_triggered = True
        elif norm_key == target:
            is_triggered = True

        if is_triggered:
            self._handle_toggle()

    def _on_release(self, key):
        norm_key = self._normalize_key(key)
        self._key_pressed_set.discard(norm_key)

    def _handle_toggle(self):
        with self.lock:
            if not self.is_recording:
                self.is_recording = True
                threading.Thread(target=play_start_tone, daemon=True).start()
                self.on_start()
            else:
                self.is_recording = False
                threading.Thread(target=play_stop_tone, daemon=True).start()
                self.on_stop()

    def start_listening(self):
        print(f"[HotkeyListener] 透過 pynput 監聽熱鍵: {self.hotkey_str}")
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.daemon = True
        self.listener.start()

    def stop_listening(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
