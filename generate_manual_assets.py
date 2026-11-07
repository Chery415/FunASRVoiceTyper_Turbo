# coding: utf-8
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = r"C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

# 載入微軟正黑體
font_title = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 22)
font_subtitle = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 17)
font_bold = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 14)
font_regular = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
font_small = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
font_code = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)


def generate_tray_menu_mock():
    """繪製 Windows 11 風格之 v3.3 系統匣完整右鍵選單與展開子選單截圖"""
    w, h = 920, 480
    img = Image.new("RGBA", (w, h), (241, 245, 249, 255))
    draw = ImageDraw.Draw(img)

    # 背景裝飾 (桌面/工作列意象)
    draw.rectangle([(0, 420), (w, 480)], fill=(226, 232, 240, 255))
    draw.line([(0, 420), (w, 420)], fill=(203, 213, 225, 255), width=1)
    draw.text((30, 440), "Windows 工作列常駐區域示意", fill=(100, 116, 139), font=font_small)

    # 系統匣圖示 FT
    tray_x, tray_y = 780, 430
    draw.ellipse([(tray_x, tray_y), (tray_x + 36, tray_y + 36)], fill=(2, 132, 199, 255))
    draw.ellipse([(tray_x + 5, tray_y + 5), (tray_x + 31, tray_y + 31)], fill=(22, 18, 30, 240))
    draw.text((tray_x + 9, tray_y + 8), "FT", fill=(2, 132, 199), font=font_bold)

    # 主選單卡片
    m_x, m_y, m_w, m_h = 390, 80, 420, 330
    # 陰影
    for offset in range(8, 0, -2):
        draw.rounded_rectangle([(m_x - offset, m_y - offset), (m_x + m_w + offset, m_y + m_h + offset)],
                               radius=10, fill=(0, 0, 0, int(15 - offset * 1.5)))
    # 主選單主體
    draw.rounded_rectangle([(m_x, m_y), (m_x + m_w, m_y + m_h)], radius=8, fill=(255, 255, 255, 250),
                           outline=(226, 232, 240, 255), width=1)

    # 主選單內容
    # Item 1: 引擎狀態 (綠點)
    draw.ellipse([(m_x + 18, m_y + 18), (m_x + 28, m_y + 28)], fill=(34, 197, 94))
    draw.text((m_x + 36, m_y + 14), "黃金引擎在線 (SenseVoice + CT標點 + Qwen-0.5B)", fill=(30, 41, 59), font=font_bold)

    # 分隔線
    draw.line([(m_x + 12, m_y + 45), (m_x + m_w - 12, m_y + 45)], fill=(241, 245, 249), width=1)

    # Item 2: 打字與段落重編模式 (高亮選中狀態)
    draw.rounded_rectangle([(m_x + 6, m_y + 52), (m_x + m_w - 6, m_y + 90)], radius=6, fill=(240, 249, 255))
    draw.text((m_x + 20, m_y + 60), "打字與段落重編模式 (Typing Mode)", fill=(2, 132, 199), font=font_bold)
    draw.text((m_x + m_w - 24, m_y + 60), "◀", fill=(2, 132, 199), font=font_bold)

    # Item 3: 快速鍵設定
    draw.text((m_x + 20, m_y + 102), "快速鍵設定 (Hotkey)", fill=(51, 65, 85), font=font_regular)
    draw.text((m_x + m_w - 24, m_y + 102), "▶", fill=(148, 163, 184), font=font_small)

    # Item 4: 開機自動啟動
    draw.text((m_x + 20, m_y + 144), "✔  開機自動啟動 (Start on Boot)", fill=(51, 65, 85), font=font_regular)

    # Item 5: 自訂專有名詞與設定
    draw.text((m_x + 20, m_y + 186), "⚙  自訂專有名詞與設定 (Config)", fill=(51, 65, 85), font=font_regular)

    # 分隔線
    draw.line([(m_x + 12, m_y + 225), (m_x + m_w - 12, m_y + 225)], fill=(241, 245, 249), width=1)

    # Item 6: 結束程式
    draw.text((m_x + 20, m_y + 238), "⏻  結束程式 (Exit)", fill=(225, 29, 72), font=font_regular)

    # 子選單卡片 (向左展開)
    sub_x, sub_y, sub_w, sub_h = 30, 60, 480, 230
    for offset in range(8, 0, -2):
        draw.rounded_rectangle([(sub_x - offset, sub_y - offset), (sub_x + sub_w + offset, sub_y + sub_h + offset)],
                               radius=10, fill=(0, 0, 0, int(15 - offset * 1.5)))
    draw.rounded_rectangle([(sub_x, sub_y), (sub_x + sub_w, sub_y + sub_h)], radius=8, fill=(255, 255, 255, 255),
                           outline=(186, 230, 253, 255), width=2)

    # 子選單標題
    draw.rounded_rectangle([(sub_x, sub_y), (sub_x + sub_w, sub_y + 36)], radius=6, fill=(240, 249, 255))
    draw.text((sub_x + 18, sub_y + 9), "v3.3 三大黃金打字模式自由切換", fill=(3, 105, 161), font=font_bold)

    # 子選單項目 1: Instant
    draw.ellipse([(sub_x + 18, sub_y + 54), (sub_x + 28, sub_y + 64)], fill=(16, 185, 129))
    draw.text((sub_x + 36, sub_y + 48), "🟢 極速打字模式 (Instant - 0ms免LLM・即時標點上屏)", fill=(51, 65, 85), font=font_regular)

    # 子選單項目 2: Typeless (選中)
    draw.rounded_rectangle([(sub_x + 6, sub_y + 82), (sub_x + sub_w - 6, sub_y + 144)], radius=6, fill=(245, 243, 255), outline=(192, 132, 252), width=1)
    draw.text((sub_x + 14, sub_y + 92), "●", fill=(147, 51, 234), font=font_bold)
    draw.ellipse([(sub_x + 28, sub_y + 96), (sub_x + 38, sub_y + 106)], fill=(168, 85, 247))
    draw.text((sub_x + 46, sub_y + 90), "🟣 流暢修訂與同音精校 (Typeless - 推薦)", fill=(126, 34, 206), font=font_bold)
    draw.text((sub_x + 46, sub_y + 116), "0.5B 秒速過濾贅詞、修正同音錯字（如程式碼/測試檔案）", fill=(107, 114, 128), font=font_small)

    # 子選單項目 3: Structured
    draw.ellipse([(sub_x + 18, sub_y + 162), (sub_x + 28, sub_y + 172)], fill=(59, 130, 246))
    draw.text((sub_x + 36, sub_y + 156), "🔵 結構化闡述與指令模式 (Structured - 重組重點)", fill=(51, 65, 85), font=font_regular)
    draw.text((sub_x + 36, sub_y + 182), "適合會議記錄與口述長文，自動提煉出標題與條列項目", fill=(100, 116, 139), font=font_small)

    # 裝飾連線
    draw.line([(sub_x + sub_w, m_y + 70), (m_x + 6, m_y + 70)], fill=(2, 132, 199), width=2)

    img.save(os.path.join(ASSETS_DIR, "v33_tray_menu.png"))
    print("✓ 已生成: v33_tray_menu.png")


def generate_modes_diagram():
    """繪製三大打字模式對比資訊圖"""
    w, h = 960, 420
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 頂部標題
    draw.rectangle([(0, 0), (w, 54)], fill=(15, 23, 42))
    draw.text((30, 14), "FunASRVoiceTyper Turbo v3.3 三大輕量打字組合與適用情境", fill=(255, 255, 255), font=font_subtitle)
    draw.text((740, 18), "三大實用語音組合", fill=(56, 189, 248), font=font_bold)

    card_w = 280
    cards_data = [
        {
            "x": 30,
            "title": "🟢 極速打字 (Instant)",
            "sub": "組合一 ｜ 0ms 免 LLM 秒出字",
            "bg": (240, 253, 244),
            "border": (34, 197, 94),
            "accent": (22, 163, 74),
            "items": [
                "• 延遲：ASR 極速 50~150ms 秒出字",
                "• 核心：SenseVoice + CT標點",
                "• Layer 1.5：聲學同音詞秒級校正",
                "• 標點：27萬詞表神經網路流暢逗句",
                "• 適用：LINE、聊天、程式碼註解、速記"
            ]
        },
        {
            "x": 340,
            "title": "🟣 流暢修訂 (Typeless) [推薦]",
            "sub": "組合二 ｜ 0.5B 極速智慧潤飾",
            "bg": (250, 245, 255),
            "border": (168, 85, 247),
            "accent": (147, 51, 234),
            "items": [
                "• 延遲：約 0.6 ~ 1.5 秒極速重構",
                "• 核心：SenseVoice + Qwen2.5-0.5B",
                "• 智慧除贅：去除「那個、嗯、然後」",
                "• 同音修復：修正「程試碼」為「程式碼」",
                "• 適用：日常信件、企劃文件、正式溝通"
            ]
        },
        {
            "x": 650,
            "title": "🔵 結構化闡述 (Structured)",
            "sub": "組合三 ｜ 口述重組條列重點",
            "bg": (239, 246, 255),
            "border": (59, 130, 246),
            "accent": (37, 99, 235),
            "items": [
                "• 延遲：約 1.5 ~ 3.5 秒條理重編",
                "• 核心：SenseVoice + Qwen2.5-0.5B",
                "• 邏輯重組：將長篇大論轉為重點清單",
                "• 自動編號：1. 2. 3. 清楚呈現執行項目",
                "• 適用：會議記錄總結、靈感腦力激盪"
            ]
        }
    ]

    for c in cards_data:
        x = c["x"]
        draw.rounded_rectangle([(x, 80), (x + card_w, 390)], radius=10, fill=c["bg"], outline=c["border"], width=2)
        # Header box
        draw.rounded_rectangle([(x, 80), (x + card_w, 136)], radius=8, fill=c["accent"])
        draw.text((x + 16, 90), c["title"], fill=(255, 255, 255), font=font_bold)
        draw.text((x + 16, 114), c["sub"], fill=(240, 249, 255), font=font_small)

        # Items
        for idx, it in enumerate(c["items"]):
            draw.text((x + 16, 155 + idx * 42), it, fill=(30, 41, 59), font=font_regular)

    img.save(os.path.join(ASSETS_DIR, "v33_modes_diagram.png"))
    print("✓ 已生成: v33_modes_diagram.png")


def generate_typing_flow_steps():
    """繪製 4 步驟開關式語音打字流程圖"""
    w, h = 960, 360
    img = Image.new("RGBA", (w, h), (248, 250, 252, 255))
    draw = ImageDraw.Draw(img)

    # 頂部標題
    draw.rectangle([(0, 0), (w, 50)], fill=(3, 105, 161))
    draw.text((30, 12), "開關切換式 (Toggle Mode) 四步驟極速打字作業流程", fill=(255, 255, 255), font=font_subtitle)
    draw.text((740, 16), "免長按・手部零負擔", fill=(224, 242, 254), font=font_bold)

    step_w = 205
    steps = [
        {
            "num": "步驟 1",
            "title": "點游標・按一下熱鍵",
            "desc": "游標置於輸入處，按一下 [右側 Ctrl] 鍵。\n聽見「叮 (1000Hz)」提示音，開始聆聽。",
            "color": (225, 29, 72),
            "pill_bg": (254, 226, 226),
            "pill_border": (239, 68, 68),
            "pill_text": "🔴 聆聽中... (紅色聲波)"
        },
        {
            "num": "步驟 2",
            "title": "自然清晰口述",
            "desc": "以正常語速講話。支援中英夾雜與數字。\n雙手完全自由，不需持續按住鍵盤！",
            "color": (13, 148, 136),
            "pill_bg": (240, 253, 250),
            "pill_border": (20, 184, 166),
            "pill_text": "🎙 支援中英混雜與數字"
        },
        {
            "num": "步驟 3",
            "title": "講完・再按一下熱鍵",
            "desc": "說話結束再按一下 [右側 Ctrl] 鍵。\n聽見「咚 (750Hz)」提示音，啟動辨識。",
            "color": (2, 132, 199),
            "pill_bg": (224, 242, 254),
            "pill_border": (14, 165, 233),
            "pill_text": "🔵 辨識中 (藍色流動光條)"
        },
        {
            "num": "步驟 4",
            "title": "文字極速自動上屏",
            "desc": "神經網路標點/同音修正完成。\n綠色打勾動畫浮現，文字自動填入！",
            "color": (22, 163, 74),
            "pill_bg": (220, 252, 231),
            "pill_border": (34, 197, 94),
            "pill_text": "✔ 辨識完成 (自動打字)"
        }
    ]

    for idx, s in enumerate(steps):
        x = 30 + idx * 230
        draw.rounded_rectangle([(x, 70), (x + step_w, 335)], radius=8, fill=(255, 255, 255),
                               outline=(203, 213, 225), width=1)

        # 步驟標籤
        draw.rounded_rectangle([(x + 12, 82), (x + 85, 106)], radius=4, fill=s["color"])
        draw.text((x + 18, 85), s["num"], fill=(255, 255, 255), font=font_small)

        # 標題
        draw.text((x + 12, 116), s["title"], fill=(15, 23, 42), font=font_bold)

        # 說明
        draw.text((x + 12, 144), s["desc"], fill=(71, 85, 105), font=font_small)

        # 膠囊示意框
        draw.rounded_rectangle([(x + 10, 275), (x + step_w - 10, 318)], radius=15, fill=s["pill_bg"],
                               outline=s["pill_border"], width=1)
        draw.text((x + 18, 288), s["pill_text"], fill=s["color"], font=font_small)

        # 箭頭
        if idx < 3:
            arr_x = x + step_w + 5
            draw.text((arr_x, 185), "➔", fill=(148, 163, 184), font=font_subtitle)

    img.save(os.path.join(ASSETS_DIR, "v33_typing_flow_steps.png"))
    print("✓ 已生成: v33_typing_flow_steps.png")


def generate_config_guide_diagram():
    """繪製 config.json 與即時熱重載示意圖"""
    w, h = 960, 420
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 頂部標題
    draw.rectangle([(0, 0), (w, 50)], fill=(30, 41, 59))
    draw.text((30, 12), "個人化設定檔 (config.json) 與即時熱重載 (Hot Reload) 機制", fill=(255, 255, 255), font=font_subtitle)
    draw.text((730, 16), "免重啟・存檔即時生效", fill=(56, 189, 248), font=font_bold)

    # 左側代碼編輯器
    c_x, c_y, c_w, c_h = 30, 75, 480, 325
    draw.rounded_rectangle([(c_x, c_y), (c_x + c_w, c_y + c_h)], radius=8, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
    # 編輯器頂部標題列
    draw.rounded_rectangle([(c_x, c_y), (c_x + c_w, c_y + 30)], radius=6, fill=(30, 41, 59))
    draw.ellipse([(c_x + 12, c_y + 10), (c_x + 20, c_y + 18)], fill=(239, 68, 68))
    draw.ellipse([(c_x + 26, c_y + 10), (c_x + 34, c_y + 18)], fill=(234, 179, 8))
    draw.ellipse([(c_x + 40, c_y + 10), (c_x + 48, c_y + 18)], fill=(34, 197, 94))
    draw.text((c_x + 60, c_y + 7), "config.json - 記事本直接編輯", fill=(203, 213, 225), font=font_small)

    code_lines = [
        '{',
        '  "hotkey": "right ctrl",',
        '  "typing_mode": "typeless",',
        '  "domain_terms": [',
        '    "台積電", "CoWoS", "EUV", "先進製程",',
        '    "AI", "API", "Meeting", "程式碼",',
        '    "城市=>程式",      // 顯式別名映射',
        '    "程試碼=>程式碼",   // 同音錯字修正',
        '    "測型檔案=>測試檔案", // 專有名詞正名',
        '    "治安=>資安",',
        '    "大竹郭小=>大竹國小"',
        '  ],',
        '  "auto_start": true',
        '}'
    ]
    for idx, l in enumerate(code_lines):
        color = (148, 163, 184)
        if "hotkey" in l or "typing_mode" in l:
            color = (56, 189, 248)
        elif "=>" in l or "//" in l:
            color = (74, 222, 128)
        elif "domain_terms" in l:
            color = (251, 191, 36)
        draw.text((c_x + 20, c_y + 40 + idx * 19), l, fill=color, font=font_code)

    # 右側特色說明卡片
    r_x, r_y, r_w, r_h = 530, 75, 400, 325
    draw.rounded_rectangle([(r_x, r_y), (r_x + r_w, r_y + r_h)], radius=8, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    draw.text((r_x + 18, r_y + 16), "⚙️ 專有名詞聲學與同音修正指南", fill=(3, 105, 161), font=font_bold)

    tips = [
        ("1. 免重啟動態重載 (Hot Reload)", "記事本編輯存檔 (Ctrl+S) 後，下一次按熱鍵錄音立即讀取套用，完全不需要重新啟動軟體！"),
        ("2. 「錯字=>正字」顯式別名映射", "支援自訂「A=>B」映射語法，系統以最高優先級執行文字替換，精準掌控特殊詞彙。"),
        ("3. 英文縮寫自動大小寫正規化", "清單中的專有名詞（如 CoWoS、EUV、API）會自動將語音識別轉出之小寫格式矯正為正確字型。"),
        ("4. 台灣國語同音相近音自動包容", "內建 DomainTermsNormalizer，自動涵蓋平捲舌音 (z/zh, c/ch, s/sh) 與前後鼻音差異。")
    ]
    for idx, (t_title, t_desc) in enumerate(tips):
        y_pos = r_y + 52 + idx * 65
        draw.text((r_x + 18, y_pos), t_title, fill=(15, 23, 42), font=font_bold)
        # 折行顯示說明
        draw.text((r_x + 18, y_pos + 22), t_desc[:26], fill=(71, 85, 105), font=font_small)
        if len(t_desc) > 26:
            draw.text((r_x + 18, y_pos + 38), t_desc[26:], fill=(71, 85, 105), font=font_small)

    img.save(os.path.join(ASSETS_DIR, "v33_config_guide.png"))
    print("✓ 已生成: v33_config_guide.png")


if __name__ == "__main__":
    generate_tray_menu_mock()
    generate_modes_diagram()
    generate_typing_flow_steps()
    generate_config_guide_diagram()
    print("All v3.3 manual assets generated successfully!")


def generate_live_typing_showcase():
    """繪製在實際應用軟體 (Word/記事本/LINE) 中使用語音打字的實境畫面展示"""
    w, h = 960, 440
    img = Image.new("RGBA", (w, h), (241, 245, 249, 255))
    draw = ImageDraw.Draw(img)

    # 頂部標題
    draw.rectangle([(0, 0), (w, 50)], fill=(15, 23, 42))
    draw.text((30, 12), "全域任意視窗即時輸入示範 (Word / LINE / 瀏覽器 / 程式碼編輯器)", fill=(255, 255, 255), font=font_subtitle)
    draw.text((750, 16), "零切換・游標即打字", fill=(56, 189, 248), font=font_bold)

    # 模擬應用視窗 (例如 Word / 編輯器)
    w_x, w_y, w_w, w_h = 40, 75, 880, 335
    draw.rounded_rectangle([(w_x, w_y), (w_x + w_w, w_y + w_h)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    # 應用程式標題列
    draw.rounded_rectangle([(w_x, w_y), (w_x + w_w, w_y + 36)], radius=6, fill=(248, 250, 252))
    draw.ellipse([(w_x + 16, w_y + 13), (w_x + 26, w_y + 23)], fill=(239, 68, 68))
    draw.ellipse([(w_x + 32, w_y + 13), (w_x + 42, w_y + 23)], fill=(234, 179, 8))
    draw.ellipse([(w_x + 48, w_y + 13), (w_x + 58, w_y + 23)], fill=(34, 197, 94))
    draw.text((w_x + 75, w_y + 8), "工作專案報告.docx - Microsoft Word / 任意文字編輯區", fill=(71, 85, 105), font=font_small)

    # 內文編輯區背景與格線
    draw.line([(w_x, w_y + 36), (w_x + w_w, w_y + 36)], fill=(226, 232, 240), width=1)

    # 內文文字示範
    sample_text_1 = "各專案負責人您好："
    sample_text_2 = "今天針對新版本系統進行驗收測試，相關進度回報如下："
    sample_text_voice = "「針對這四個資訊安全工具的測試，個別建立一個資料夾，裡面要包含預計要測試下載的程式碼或者測試檔案。」"
    
    draw.text((w_x + 36, w_y + 60), sample_text_1, fill=(100, 116, 139), font=font_regular)
    draw.text((w_x + 36, w_y + 95), sample_text_2, fill=(100, 116, 139), font=font_regular)

    # 語音自動打上螢幕的高亮效果
    draw.rounded_rectangle([(w_x + 30, w_y + 135), (w_x + w_w - 30, w_y + 205)], radius=6, fill=(240, 253, 250), outline=(45, 212, 191), width=1)
    draw.text((w_x + 42, w_y + 145), "▼ 口述語音自動上屏（已自動加入標點與專有名詞校正）：", fill=(13, 148, 136), font=font_small)
    draw.text((w_x + 42, w_y + 170), sample_text_voice, fill=(15, 23, 42), font=font_bold)
    # 閃爍游標 |
    draw.line([(w_x + 825, w_y + 168), (w_x + 825, w_y + 192)], fill=(2, 132, 199), width=2)

    # 浮動懸浮膠囊資訊 (Floating Capsule Overlay)
    c_x, c_y, c_w, c_h = 240, w_y + 235, 480, 70
    draw.rounded_rectangle([(c_x, c_y), (c_x + c_w, c_y + c_h)], radius=35, fill=(15, 23, 42, 240), outline=(56, 189, 248), width=2)
    # 打勾圖示
    draw.ellipse([(c_x + 18, c_y + 17), (c_x + 52, c_y + 51)], fill=(34, 197, 94))
    draw.text((c_x + 26, c_y + 20), "✔", fill=(255, 255, 255), font=font_bold)
    # 統計字樣
    draw.text((c_x + 65, c_y + 16), "語音辨識與精校完成 (自動輸入成功)", fill=(240, 249, 255), font=font_bold)
    draw.text((c_x + 65, c_y + 38), "ASR: 68ms | LLM: 520ms | 模式: Typeless (Qwen2.5-0.5B)", fill=(148, 163, 184), font=font_small)

    img.save(os.path.join(ASSETS_DIR, "v33_live_typing_showcase.png"))
    print("✓ 已生成: v33_live_typing_showcase.png")

if __name__ == "__main__":
    generate_live_typing_showcase()
