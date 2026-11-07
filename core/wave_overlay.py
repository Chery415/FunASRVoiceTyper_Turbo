import tkinter as tk
import threading
import math

class WaveOverlay:
    """
    螢幕浮動膠囊狀態條 (LocalVoiceTyper_SenseVoice 專屬)：
    - 錄音中 (Recording)：🔴 聆聽中... + 動態跳動音波
    - 辨識中 (Processing)：⚡ SenseVoice + LLM 校正中... + 流光動畫
    - 完成 (Success)：✓ 校正完成 (短暫停留 350ms 後優雅隱藏)
    """
    def __init__(self, get_level_func=None):
        self.get_level_func = get_level_func
        self.root = None
        self.canvas = None
        self.is_visible = False
        self.state = "recording"
        self.phase = 0.0
        self._thread = threading.Thread(target=self._run_ui, daemon=True)
        self._thread.start()

    def _run_ui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.94)

        self.width = 300
        self.height = 46

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - self.width) // 2
        y = screen_h - self.height - 45
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        bg_color = "#121316"
        self.root.configure(bg=bg_color)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.root.withdraw()
        self._animate()
        self.root.mainloop()

    def show_recording(self):
        self.state = "recording"
        self.is_visible = True
        if self.root:
            self.root.after(0, self.root.deiconify)

    def show_processing(self):
        self.state = "processing"
        self.is_visible = True
        if self.root:
            self.root.after(0, self.root.deiconify)

    def show_success(self, duration_ms=350):
        self.state = "success"
        if self.root:
            self.root.after(0, self.root.deiconify)
        threading.Timer(duration_ms / 1000.0, self.hide).start()

    def hide(self):
        self.is_visible = False
        if self.root:
            self.root.after(0, self.root.withdraw)

    def _animate(self):
        if self.is_visible and self.canvas:
            self.canvas.delete("all")

            self.canvas.create_rectangle(
                2, 2, self.width - 2, self.height - 2,
                outline="#2A2C33", width=1.5
            )

            center_y = self.height / 2
            self.phase += 0.25

            if self.state == "recording":
                self.canvas.create_oval(18, 19, 26, 27, fill="#FF453A", outline="")
                self.canvas.create_text(
                    65, 23,
                    text="聆聽中...",
                    fill="#FFFFFF",
                    font=("Segoe UI", 9, "bold")
                )

                level = self.get_level_func() if self.get_level_func else 0.15
                level = max(0.08, min(level, 1.0))

                num_bars = 16
                start_x = 115
                bar_w = 4
                gap = 5
                max_bar_h = 24

                for i in range(num_bars):
                    wave = math.sin(self.phase + i * 0.45)
                    h = 4 + (abs(wave) * max_bar_h * (level * 2.2))
                    h = min(max_bar_h, max(4, h))

                    x0 = start_x + i * (bar_w + gap)
                    y0 = center_y - (h / 2)
                    x1 = x0 + bar_w
                    y1 = center_y + (h / 2)

                    color = "#A855F7" if i % 2 == 0 else "#6366F1"
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

            elif self.state == "processing":
                dot_color = "#A855F7" if int(self.phase * 2) % 2 == 0 else "#6366F1"
                self.canvas.create_oval(18, 19, 26, 27, fill=dot_color, outline="")
                
                dots = "." * ((int(self.phase) % 3) + 1)
                self.canvas.create_text(
                    142, 23,
                    text=f"語音辨識 + 段落重編中{dots}",
                    fill="#F3E8FF",
                    font=("Segoe UI", 9, "bold")
                )

                spin_x = 270
                for idx in range(4):
                    ang = self.phase + idx * (math.pi / 2)
                    px = spin_x + math.cos(ang) * 7
                    py = center_y + math.sin(ang) * 7
                    col = "#A855F7" if idx == 0 else "#404040"
                    self.canvas.create_oval(px - 1.5, py - 1.5, px + 1.5, py + 1.5, fill=col, outline="")

            elif self.state == "success":
                self.canvas.create_oval(18, 19, 26, 27, fill="#30D158", outline="")
                self.canvas.create_text(
                    150, 23,
                    text="✓ 雙階段校正完成，已輸入",
                    fill="#30D158",
                    font=("Segoe UI", 9, "bold")
                )

        if self.root:
            self.root.after(30, self._animate)
