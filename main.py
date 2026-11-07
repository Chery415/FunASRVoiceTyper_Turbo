"""
FunASRVoiceTyper_Turbo v3.3 (Lean Golden Edition):
專注於實測綜合表現最佳之黃金組合 (組合 16 / 17 / 18)：
- 語音與標點引擎：固定採用 SenseVoice-Small (ONNX) + CT-Transformer 標點大模型
- 語意重構引擎：固定採用內嵌 Qwen2.5-0.5B-Instruct (GGUF)
- 系統托盤選單：移除多餘的模型切換子選單，僅保留核心 3 種打字模式 (Instant / Typeless / Structured) 與系統設定
"""

import os
import sys
import json
import ctypes
import tempfile
import threading
import subprocess
from PIL import Image, ImageDraw
import pystray
import soundfile as sf

import logging
from core.autostart import is_auto_start_enabled, set_auto_start
from core.audio_recorder import AudioRecorder
from core.pipeline import HybridSpeechPipeline
from core.text_injector import TextInjector
from core.hotkey_listener import ToggleVoiceController
from core.wave_overlay import WaveOverlay

CONFIG_FILENAME = "config.json"
_SINGLE_INSTANCE_MUTEX = None


def acquire_single_instance_lock() -> bool:
    global _SINGLE_INSTANCE_MUTEX
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\FunASRVoiceTyper_Turbo_SingleInstance_Mutex_v3"
        handle = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == 183:
            return False
        _SINGLE_INSTANCE_MUTEX = handle
        return True
    except Exception:
        return True


def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.join(get_app_dir(), CONFIG_FILENAME)


def setup_logging():
    log_file = os.path.join(get_app_dir(), "app.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
        force=True
    )
    logging.info("==========================================")
    logging.info("  FunASRVoiceTyper_Turbo v3.3 黃金輕量版日誌已啟動")
    logging.info("==========================================")

    class StdoutRedirector:
        def __init__(self, logger_func, stream=None):
            self.logger_func = logger_func
            self.stream = stream
            self.buf = ""

        def write(self, s):
            if self.stream:
                try:
                    self.stream.write(s)
                except Exception:
                    pass
            self.buf += s
            if "\n" in self.buf:
                parts = self.buf.split("\n")
                for p in parts[:-1]:
                    if p.strip():
                        self.logger_func(p)
                self.buf = parts[-1]

        def flush(self):
            if self.stream:
                try:
                    self.stream.flush()
                except Exception:
                    pass
            if self.buf.strip():
                self.logger_func(self.buf)
                self.buf = ""

    sys.stdout = StdoutRedirector(logging.info, sys.stdout)
    sys.stderr = StdoutRedirector(logging.error, sys.stderr)


setup_logging()


def load_config() -> dict:
    cfg_path = get_config_path()
    default_cfg = {
        "hotkey": "right ctrl",
        "language": "zh",
        "asr_model_id": "SenseVoice-Small",
        "llm_backend": "embedded",
        "llm_gguf_path": "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "llm_api_base": "http://localhost:11434/v1",
        "llm_model_name": "qwen2.5:0.5b-instruct-q4_K_M",
        "llm_api_key": "",
        "domain_terms": [
            "台積電", "CoWoS", "EUV", "先進製程", "晶圓代工", "半導體",
            "AI", "API", "Agent", "Meeting", "GitHub", "SFTPGo",
            "Windows", "Ubuntu", "Linux", "Google Antigravity", "Antigravity",
            "Claude Code", "Gemini", "指令碼", "程式碼", "測試檔案", "資安工具", "資安", "模型",
            "大竹國小", "韓風熱舞社", "標點符號", "語音辨識", "辨識速度",
            "城市=>程式", "層次碼=>程式碼", "程試碼=>程式碼", "測試碼=>程式碼",
            "測型檔案=>測試檔案", "測行檔案=>測試檔案", "測告=>測試", "裡麵=>裡面",
            "治安=>資安", "辨試=>辨識", "變試=>辨識", "面試的速度=>辨識的速度",
            "大竹郭小=>大竹國小", "大主播小=>大竹國小", "寒風熱舞室=>韓風熱舞社",
            "gmin=>Gemini", "integravity=>Antigravity", "cloucoo=>Claude Code", "reno 4=>Linux"
        ],
        "enable_correction": True,
        "min_llm_char_length": 2,
        "llm_timeout_seconds": 6.0,
        "typeless_timeout_seconds": 10.0,
        "typing_mode": "typeless",
        "auto_start": False
    }
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8-sig") as f:
            json.dump(default_cfg, f, indent=2, ensure_ascii=False)
        return default_cfg
    try:
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            for k, v in default_cfg.items():
                if k not in data:
                    data[k] = v
            data["asr_model_id"] = "SenseVoice-Small"
            data["llm_gguf_path"] = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
            return data
    except Exception:
        return default_cfg


def save_config(cfg: dict):
    cfg_path = get_config_path()
    with open(cfg_path, "w", encoding="utf-8-sig") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def create_tray_icon(primary_color: str, text: str = "FT") -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 60, 60), fill=primary_color)
    draw.ellipse((14, 14, 50, 50), fill=(22, 18, 30, 230))
    draw.text((22, 23), text, fill=primary_color)
    return image


class HybridVoiceTyperApp:
    def __init__(self):
        logging.info("初始化 HybridVoiceTyperApp v3.3 (黃金輕量版)...")
        self.config = load_config()
        self.recorder = AudioRecorder()
        self.injector = TextInjector()
        self.wave_overlay = WaveOverlay(get_level_func=self.recorder.get_volume)

        self.idle_icon = create_tray_icon("#0284C7", "FT")
        self.loading_icon = create_tray_icon("#888888", "...")
        self.recording_icon = create_tray_icon("#FF3B30", "REC")
        self.error_icon = create_tray_icon("#E11D48", "ERR")

        self.is_model_ready = False
        self.pipeline = None
        self.is_processing = False
        self.controller = None
        self.tray_icon = None
        self._init_controller()

        threading.Thread(target=self._load_pipeline_async, daemon=True).start()

    def _load_pipeline_async(self):
        print("[HybridApp] 正在背景非同步預載入 SenseVoice-Small、CT-Transformer 標點與 Qwen2.5-0.5B 引擎...")
        try:
            self.pipeline = HybridSpeechPipeline(
                asr_model_id="SenseVoice-Small",
                llm_api_base=self.config.get("llm_api_base", "http://localhost:11434/v1"),
                llm_model_name="qwen2.5:0.5b-instruct-q4_K_M",
                device="cpu",
                llm_api_key=self.config.get("llm_api_key", ""),
                llm_backend=self.config.get("llm_backend", "embedded"),
                llm_gguf_path="models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
            )
            if self.pipeline.is_llm_online():
                self.pipeline.warmup_llm()
            else:
                logging.warning("[HybridApp] ⚠️ LLM 引擎未就緒，將僅使用 SenseVoice + CT標點 + Layer 1.5 規則校正。")

            self.is_model_ready = True
            print("[HybridApp] SenseVoice-Small + CT標點 + Qwen2.5-0.5B 黃金組合載入就緒！")
            try:
                import winsound
                winsound.Beep(1200, 100)
            except Exception:
                pass
            self.update_tray(recording=False)
            if self.tray_icon:
                try:
                    self.tray_icon.update_menu()
                except Exception:
                    pass
        except Exception as e:
            import traceback
            err_msg = f"[HybridApp] 引擎載入錯誤: {e}\n{traceback.format_exc()}"
            print(err_msg)
            logging.error(err_msg)
            if self.tray_icon:
                self.tray_icon.icon = self.error_icon
                self.tray_icon.title = f"SpeechPipeline [載入錯誤: {e}]"

    def _init_controller(self):
        current_hotkey = self.config.get("hotkey", "right ctrl")
        self.controller = ToggleVoiceController(
            hotkey=current_hotkey,
            on_start=self.on_start_recording,
            on_stop=self.on_stop_recording
        )

    def reload_config_if_modified(self):
        cfg_path = get_config_path()
        try:
            if os.path.exists(cfg_path):
                mtime = os.path.getmtime(cfg_path)
                if not hasattr(self, '_last_cfg_mtime') or mtime > self._last_cfg_mtime:
                    self._last_cfg_mtime = mtime
                    fresh_cfg = load_config()
                    old_hotkey = self.config.get("hotkey", "").lower()
                    new_hotkey = fresh_cfg.get("hotkey", "").lower()
                    self.config = fresh_cfg
                    if old_hotkey != new_hotkey and self.controller:
                        logging.info(f"[Config] 偵測到熱鍵更新: {old_hotkey} -> {new_hotkey}")
                        self.change_hotkey(new_hotkey)
                    terms_count = len(self.config.get("domain_terms", []))
                    logging.info(f"[Config] 已即時動態載入最新設定！自訂專有名詞數量: {terms_count}")
        except Exception as e:
            logging.error(f"[Config] 動態讀取設定檔例外: {e}")

    def on_start_recording(self):
        self.reload_config_if_modified()
        if not self.is_model_ready:
            print("[HybridApp] ⚠️ 語音模型仍在載入與預熱中，請稍候 1~2 秒...")
            try:
                import winsound
                winsound.Beep(400, 150)
            except Exception:
                pass
            return

        print("\n[HybridApp] 🔴 開始錄音...")
        self.update_tray(recording=True)
        self.wave_overlay.show_recording()
        self.recorder.start()

    def on_stop_recording(self):
        self.reload_config_if_modified()
        print("[HybridApp] ⏹️ 停止錄音，轉錄與標點精校中...")
        self.wave_overlay.show_processing()
        self.update_tray(recording=False)
        audio = self.recorder.stop()

        def _worker():
            self.is_processing = True
            temp_wav_path = None
            try:
                if len(audio) < 16000 * 0.2:
                    print("[HybridApp] ⚠️ 音訊過短")
                    self.wave_overlay.hide()
                    return

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    temp_wav_path = tmp.name
                    sf.write(temp_wav_path, audio, 16000)

                self.reload_config_if_modified()
                domain_terms = self.config.get("domain_terms", [])
                enable_correction = self.config.get("enable_correction", True)
                typing_mode = self.config.get("typing_mode", "typeless")
                min_llm_len = int(self.config.get("min_llm_char_length", 2))

                if typing_mode in ("typeless", "structured"):
                    llm_timeout_seconds = float(self.config.get("typeless_timeout_seconds", 10.0))
                else:
                    llm_timeout_seconds = float(self.config.get("llm_timeout_seconds", 6.0))

                res = self.pipeline.process(
                    audio_path=temp_wav_path,
                    domain_terms=domain_terms,
                    enable_correction=enable_correction,
                    llm_timeout_seconds=llm_timeout_seconds,
                    typing_mode=typing_mode,
                    min_llm_char_length=min_llm_len
                )

                if res.final_text:
                    fallback_info = " (規則備援)" if res.is_fallback else ""
                    print(
                        f"[HybridApp] ✓ 轉錄完成 [ASR:{res.asr_latency_ms:.1f}ms, "
                        f"LLM:{res.llm_latency_ms:.1f}ms, 總計:{res.total_latency_ms:.1f}ms{fallback_info}]: "
                        f"{res.final_text}"
                    )
                    self.injector.inject_text(res.final_text)
                    self.wave_overlay.show_success(duration_ms=350)
                else:
                    print("[HybridApp] ⚠️ 未辨識出有效文字")
                    self.wave_overlay.hide()
            except Exception as e:
                print(f"[HybridApp] ❌ 處理錯誤: {e}")
                self.wave_overlay.hide()
            finally:
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.remove(temp_wav_path)
                    except Exception:
                        pass
                self.is_processing = False

        threading.Thread(target=_worker, daemon=True).start()

    def update_tray(self, recording: bool):
        if self.tray_icon:
            hotkey_name = self.config.get('hotkey', 'right ctrl').upper()
            mode_label = self.config.get('typing_mode', 'typeless')
            if not self.is_model_ready:
                self.tray_icon.icon = self.loading_icon
                self.tray_icon.title = "FunASRVoiceTyper Turbo (模型載入預熱中...)"
            else:
                self.tray_icon.icon = self.recording_icon if recording else self.idle_icon
                title = (
                    "FunASRVoiceTyper Turbo (錄音中...)"
                    if recording
                    else f"FunASRVoiceTyper Turbo (SenseVoice+0.5B | {mode_label} | 熱鍵: {hotkey_name})"
                )
                self.tray_icon.title = title

    def change_typing_mode(self, mode_name: str):
        try:
            self.reload_config_if_modified()
            self.config["typing_mode"] = mode_name
            save_config(self.config)
            print(f"[HybridApp] ✓ 打字模式切換成功: {mode_name} (KV Cache 保持常駐不失效)")
            self.update_tray(recording=False)
            if self.tray_icon:
                self.tray_icon.update_menu()
        except Exception as e:
            print(f"[HybridApp] 切換打字模式失敗: {e}")

    def change_hotkey(self, new_hotkey: str):
        try:
            self.controller.stop_listening()
            self.reload_config_if_modified()
            self.config["hotkey"] = new_hotkey
            save_config(self.config)
            self._init_controller()
            self.controller.start_listening()
            self.update_tray(recording=False)
            if self.tray_icon:
                self.tray_icon.update_menu()
            print(f"[HybridApp] 熱鍵已更新為: {new_hotkey}")
        except Exception as e:
            print(f"[HybridApp] 更新熱鍵失敗: {e}")

    def toggle_autostart(self, icon, item):
        current = is_auto_start_enabled()
        new_state = not current
        set_auto_start(new_state)
        self.config["auto_start"] = new_state
        save_config(self.config)
        icon.update_menu()

    def open_config(self, icon, item):
        cfg_path = get_config_path()
        try:
            os.startfile(cfg_path)
        except Exception:
            subprocess.run(["notepad.exe", cfg_path])

    def exit_app(self, icon, item):
        print("[HybridApp] 正在退出程式...")
        self.controller.stop_listening()
        self.wave_overlay.hide()
        icon.stop()

    def _is_llm_online(self) -> bool:
        if self.pipeline is not None:
            return self.pipeline.is_llm_online()
        return False

    def run(self):
        self.controller.start_listening()

        def make_setter(key_name):
            return lambda icon, item: self.change_hotkey(key_name)

        def is_current(key_name):
            return lambda item: self.config.get("hotkey", "").lower() == key_name.lower()

        def make_mode_setter(mode_val):
            return lambda icon, item: self.change_typing_mode(mode_val)

        def is_mode_current(mode_val):
            return lambda item: self.config.get("typing_mode", "typeless").lower() == mode_val.lower()

        def get_engine_status_text(item):
            online = self._is_llm_online()
            if online and self.pipeline:
                return "🟢 黃金引擎在線 (SenseVoice-Small + CT標點 + Qwen2.5-0.5B)"
            return "⚪ 引擎載入中或僅用本機規則"

        menu = pystray.Menu(
            pystray.MenuItem(get_engine_status_text, lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "打字與段落重編模式 (Typing Mode)",
                pystray.Menu(
                    pystray.MenuItem(
                        "🟢 極速打字模式 (Instant - 0ms免LLM・即時標點上屏)",
                        make_mode_setter("instant"),
                        checked=is_mode_current("instant"),
                        radio=True
                    ),
                    pystray.MenuItem(
                        "🟣 流暢修訂與同音精校 (Typeless - 0.5B極速修錯字/潤飾 - 推薦)",
                        make_mode_setter("typeless"),
                        checked=is_mode_current("typeless"),
                        radio=True
                    ),
                    pystray.MenuItem(
                        "🔵 結構化闡述與指令模式 (Structured - 長篇重組為條理重點)",
                        make_mode_setter("structured"),
                        checked=is_mode_current("structured"),
                        radio=True
                    )
                )
            ),
            pystray.MenuItem(
                "快速鍵設定 (Hotkey)",
                pystray.Menu(
                    pystray.MenuItem("右側 Ctrl (Right Ctrl - 推薦)", make_setter("right ctrl"), checked=is_current("right ctrl"), radio=True),
                    pystray.MenuItem("右側 Alt (Right Alt)", make_setter("right alt"), checked=is_current("right alt"), radio=True),
                    pystray.MenuItem("F8 鍵", make_setter("f8"), checked=is_current("f8"), radio=True),
                    pystray.MenuItem("開啟設定檔手動自訂...", self.open_config)
                )
            ),
            pystray.MenuItem(
                "開機自動啟動 (Start on Boot)",
                self.toggle_autostart,
                checked=lambda item: is_auto_start_enabled()
            ),
            pystray.MenuItem("自訂專有名詞與設定 (Config)", self.open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("結束程式 (Exit)", self.exit_app)
        )

        hotkey_name = self.config.get('hotkey', 'right ctrl').upper()
        mode_label = self.config.get('typing_mode', 'typeless')
        current_icon = self.idle_icon if self.is_model_ready else self.loading_icon
        current_title = (
            f"FunASRVoiceTyper Turbo (SenseVoice+0.5B | {mode_label} | 熱鍵: {hotkey_name})"
            if self.is_model_ready
            else "FunASRVoiceTyper Turbo (模型載入預熱中...)"
        )
        self.tray_icon = pystray.Icon(
            "FunASRVoiceTyper_Turbo",
            current_icon,
            current_title,
            menu=menu
        )

        print(f"[App] FunASRVoiceTyper Turbo v3.3 啟動成功！常駐熱鍵: {hotkey_name}")
        self.tray_icon.run()


if __name__ == "__main__":
    if not acquire_single_instance_lock():
        print("[App] 偵測到 FunASRVoiceTyper_Turbo 已經在背景執行中，本次啟動自動略過以避免重複載入。")
        sys.exit(0)
    app = HybridVoiceTyperApp()
    app.run()
