# coding: utf-8
import os
import sys
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def build_manual_docx():
    target_dir = r"C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo"
    doc = docx.Document()

    # 設置頁面邊距
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.different_first_page_header_footer = False

    # 調色盤
    PRIMARY_COLOR = RGBColor(2, 132, 199)       # 天藍 #0284C7
    PRIMARY_DARK = RGBColor(3, 105, 161)        # 深天藍 #0369A1
    NAVY_DARK = RGBColor(15, 23, 42)            # 深海藍黑 #0F172A
    TEXT_DARK = RGBColor(30, 41, 59)            # 內文深灰 #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)        # 註解次要灰 #64748B
    ACCENT_PURPLE = RGBColor(126, 34, 206)      # 紫色 #7E22CE
    ACCENT_GREEN = RGBColor(22, 163, 74)        # 綠色 #16A34A
    ACCENT_RED = RGBColor(225, 29, 72)          # 紅色 #E11D48

    def set_font(run, font_name='微軟正黑體', size_pt=10.5, color=TEXT_DARK, bold=False, italic=False):
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(size_pt)
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.italic = italic

    def add_p(text="", space_before=0, space_after=5, align=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.15):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            r = p.add_run(text)
            set_font(r)
        return p

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=15.5, color=NAVY_DARK, bold=True)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(13)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=12.5, color=PRIMARY_DARK, bold=True)
        return p

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=11, color=TEXT_DARK, bold=True)
        return p

    def add_callout(title, lines, border_color="0284C7", bg_color="F0F9FF"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
                <w:top w:val="none"/>
                <w:right w:val="none"/>
                <w:bottom w:val="none"/>
            </w:tcBorders>
        ''')
        cell._tc.get_or_add_tcPr().append(borders)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Inches(0.12)
        p.paragraph_format.right_indent = Inches(0.12)
        r_title = p.add_run(f"{title}\n")
        set_font(r_title, size_pt=11, color=NAVY_DARK, bold=True)
        for idx, line in enumerate(lines):
            r_line = p.add_run(line + ("\n" if idx < len(lines)-1 else ""))
            set_font(r_line, size_pt=10, color=TEXT_DARK)
        add_p("", space_before=0, space_after=3)

    def add_image_box(img_rel_path, caption, width_in=5.5):
        img_path = os.path.join(target_dir, img_rel_path)
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.add_run().add_picture(img_path, width=Inches(width_in))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(1)
            p_cap.paragraph_format.space_after = Pt(8)
            r_cap = p_cap.add_run(f"▲ {caption}")
            set_font(r_cap, size_pt=9.5, color=TEXT_MUTED, italic=True)
        else:
            print(f"[Warning] Image not found: {img_path}")

    # ==========================
    # 文件封面與標題
    # ==========================
    p_title = add_p("", space_before=16, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_main_title = p_title.add_run("FunASRVoiceTyper Turbo v3.3\n")
    set_font(r_main_title, size_pt=24, color=NAVY_DARK, bold=True)
    r_sub_title = p_title.add_run("黃金輕量專用版・全域開關式極速打字使用者操作手冊\n")
    set_font(r_sub_title, size_pt=14, color=PRIMARY_DARK, bold=True)
    r_ver_info = p_title.add_run("SenseVoice-Small 語音大模型 ＋ CT-Transformer 標點 ＋ 內嵌 Qwen2.5-0.5B 語意精校")
    set_font(r_ver_info, size_pt=10.5, color=TEXT_MUTED)

    add_callout(
        "🌟 v3.3 黃金輕量版核心特色總覽",
        [
            "• 極致輕量化純本機架構：本版本已全面剔除所有不需要的繁雜與肥大模型，專案結構大幅瘦身，純粹聚焦於本機極速打字核心。固定採用一套 SenseVoice-Small (ONNX) 語音模型 ＋ 27 萬詞表 CT-Transformer 中文標點大模型，搭配內嵌超輕量 Qwen2.5-0.5B 語意精校引擎，達到極速秒出字與極致資源精簡。",
            "• 僅保留三大專用打字模式組合：系統目前僅提供【組合一：Instant 極速打字 (0ms 免 LLM)】、【組合二：Typeless 流暢修訂 (0.5B 秒速精校・推薦)】與【組合三：Structured 結構化闡述 (口述長文提煉重點)】三大組合，使用者無須在眾多複雜模型中抉擇，開箱即享最實用的打字體驗。",
            "• 開關切換式操作 (Toggle Mode)：按一下熱鍵（預設右側 Ctrl）清脆提示音開始錄音，說完再按一下沉穩提示音結束並自動打字上屏，告別按住不放的手部疲勞與衝突判定！",
            "• 專有名詞聲學智慧修正：內建 Layer 1.5 專有名詞修正器，支援「錯字=>正字」別名映射、科技英文大小寫自動正規化，並自動包容台灣國語平捲舌與前後鼻音差異。",
            "• 100% 離線純本機推論：零網路連線依賴、零音訊外部上傳，實體隔離拔網線 (Air-Gap) 依舊毫秒級運作，徹底保障個人隱私與企業機密資安！"
        ],
        border_color="0284C7",
        bg_color="F0F9FF"
    )

    # 實境打字展示圖
    add_image_box("assets/v33_live_typing_showcase.png", "圖 0-1：FunASRVoiceTyper Turbo v3.3 在微軟 Word 及任意視窗中之實境語音打字展示", width_in=5.8)

    # ==========================
    # 第一章 系統架構與三大打字模式
    # ==========================
    add_heading_1("第一章 系統架構與三大打字模式組合深度解析")
    add_p("FunASRVoiceTyper Turbo 最新修訂版為極致輕量化專用設計，已將所有不需要的多餘模型全數移除，專案結構大幅瘦身，目前全系統僅精準收斂為「三大實用打字組合」。使用者無須再手動設定或挑選底層複雜的模型引擎，開箱即可透過工作列系統匣選單，隨時依當前的工作與對話情境一鍵切換最適組合：")

    add_heading_2("1.1 輕量化核心模型架構")
    add_p("本系統僅保留並載入三項經高度量化的核心輕量模型，確保開機秒速啟動與極低記憶體佔用：")
    add_p("1. 主語音識別引擎 (ASR)：SenseVoice-Small ONNX 旗艦量化版（約 230 MB），具備極低非自回歸推論延遲（<70ms），繁體中文與台灣慣用語辨識率優異。")
    add_p("2. 獨立標點神經網絡 (Punc)：CT-Transformer 27 萬詞表中文標點大模型（約 270 MB），自動依語意上下文插入全形逗號與句號，標點自然流暢。")
    add_p("3. 內嵌語意重構引擎 (LLM)：Qwen2.5-0.5B-Instruct Q4_K_M（約 397 MB），極度輕量高效，純 CPU 即可在 0.5 秒內完成口語贅詞過濾與同音錯字修訂。")

    add_heading_2("1.2 僅保留之三大打字模式組合解析")
    add_p("使用者可透過工作列系統匣圖示隨時無縫切換三大打字組合，滿足從極速即時聊天到正式會議總結的各種需求：")

    add_image_box("assets/v33_modes_diagram.png", "圖 1-1：三大輕量打字組合特色與適用情境對比圖", width_in=5.8)

    # 模式比較表
    table = doc.add_table(rows=4, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["打字模式組合", "核心架構機制", "平均上屏延遲", "最佳適用情境"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="0369A1"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size_pt=9.5, color=RGBColor(255, 255, 255), bold=True)

    mode_rows = [
        ("組合一：\n🟢 Instant 極速打字", "SenseVoice + CT標點 + Layer 1.5 專有名詞聲學校正 (完全跳過 LLM)", "50 ~ 150 ms\n(極速秒出字)", "LINE/Slack 即時通訊、社群聊天、程式碼註解、日常短句速記"),
        ("組合二：\n🟣 Typeless 流暢修訂\n(預設推薦)", "SenseVoice + CT標點 + Qwen2.5-0.5B 輕量重構，自動過濾口語贅詞與修復同音錯字", "0.6 ~ 1.5 秒\n(流暢自然)", "商務電子郵件、專案企劃報告、行政公文撰寫、團隊會議溝通"),
        ("組合三：\n🔵 Structured 結構化", "SenseVoice + Qwen2.5-0.5B 結構化 Prompt，將口述長文自動提煉為條列項目與標題", "1.5 ~ 3.5 秒\n(重點條理分明)", "會議記錄總結、待辦清單整理、腦力激盪重點條列、長篇演講筆記")
    ]
    for r_idx, row in enumerate(mode_rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="F8FAFC"/>')
                cell._tc.get_or_add_tcPr().append(shd)
            p = cell.paragraphs[0]
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                set_font(r, size_pt=9, color=NAVY_DARK, bold=True)
            elif c_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                set_font(r, size_pt=9, color=PRIMARY_DARK, bold=True)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=9, color=TEXT_DARK)

    add_p("", space_before=4, space_after=6)

    # ==========================
    # 第二章 快速安裝與常駐配置
    # ==========================
    add_heading_1("第二章 快速安裝與開機自動常駐")
    add_p("FunASRVoiceTyper_Turbo 採用免安裝 Python 環境的綠色封裝架構。所有依賴庫、ONNX 執行時與神經網路權重皆已內建於發行套件中，解壓縮後即可一鍵自動化安裝。")

    add_heading_2("2.1 一鍵自動安裝步驟")
    add_p("1. 取得發行壓縮包並解壓縮至任意目錄（例如桌面或個人資料夾）。")
    add_p("2. 進入資料夾，找到「Setup_安裝與開機啟動.bat」腳本。")
    add_p("3. 滑鼠左鍵雙擊啟動（或按右鍵選擇『以系統管理員身分執行』）。")
    add_p("4. 安裝精靈將自動在背景完成以下作業：")
    add_p("   • 自動關閉執行中的舊版程序，並將完整程式與模型部署至標準使用者目錄：%LOCALAPPDATA%\\Programs\\FunASRVoiceTyper_Turbo。")
    add_p("   • 寫入 Windows 註冊表開機啟動項目 (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)，確保每次重新開機自動背景常駐。")
    add_p("   • 自動於桌面與 Windows「開始」功能表建立「FunASRVoiceTyper Turbo」快捷方式。")
    add_p("   • 自動啟動程式，右下角系統匣將即刻出現藍色「FT」圖示，並以一聲短促嗶聲確認模型就緒。")

    add_heading_2("2.2 完整解除安裝程序")
    add_p("若需完全移除軟體，只需點擊目錄中的「Uninstall_解除安裝.bat」：")
    add_p("• 解除安裝精靈會安全終止所有相關背景程序。")
    add_p("• 清理註冊表開機啟動項、桌面快捷方式與開始功能表捷徑。")
    add_p("• 徹底刪除程式目錄與暫存檔案，不留任何系統垃圾，100% 乾淨無殘留。")

    # ==========================
    # 第三章 核心操作規範 (Toggle Mode)
    # ==========================
    add_heading_1("第三章 語音打字核心操作規範 (開關式 Toggle Mode)")

    add_callout(
        "⚠️ 重要操作觀念：開關切換式 (Toggle Mode) 與長按模式之差異",
        [
            "本軟體特別採用【開關切換式 (Toggle Mode)】操作邏輯，【絕對不要】按住熱鍵不放！",
            "✔ 正確手勢：按一下右側 Ctrl 鍵立即放開手，開始自然講話；講完後，再按一下右側 Ctrl 鍵立即放開，文字自動秒速打上螢幕。",
            "✔ 效益：說話過程中雙手 100% 自由放鬆，避免長時間按壓鍵盤手指疲勞，更杜絕了鍵盤按鍵重複送出（Key-Repeat）導致錄音被誤判中斷的問題。"
        ],
        border_color="EF4444",
        bg_color="FEF2F2"
    )

    add_image_box("assets/keyboard_hotkey.png", "圖 3-1：標準鍵盤之 [右側 Ctrl] 鍵推薦配置與開關式操作示意", width_in=5.4)

    add_heading_2("3.1 四步驟標準打字作業流程")
    add_image_box("assets/v33_typing_flow_steps.png", "圖 3-2：開關切換式 (Toggle Mode) 四步驟極速打字流程圖", width_in=5.8)

    add_heading_3("【步驟一：定位游標並啟動聆聽】")
    add_p("將文字輸入游標點在任何需要打字的視窗中（例如 Word、LINE 聊天視窗、Teams、瀏覽器網址列、記事本、VS Code 或終端機）。輕按一下鍵盤上的 [右側 Ctrl] 鍵。此時耳機會聽見清脆的高頻「叮（1000Hz）」提示音，螢幕正下方將浮現紅色脈動麥克風波形膠囊。")
    add_image_box("assets/ref_images/image2.png", "圖 3-3：聆聽中狀態——螢幕底部紅色脈動麥克風聲波膠囊（高頻提示音：叮 1000Hz）", width_in=3.0)

    add_heading_3("【步驟二：以正常語速自然說話】")
    add_p("對麥克風自然口述即可。系統全面支援：")
    add_p("• 中英文夾雜混說：例如「請把這份 API 文件發到 Teams 群組，讓工程師 Review」。")
    add_p("• 數字、年份與百分比自動正規化 (ITN)：例如口述「產能提升百分之八十」，系統自動輸出「產能提升 80%」。")
    add_p("• 台灣慣用語與專有名詞：精準對應台灣用詞習慣，絕不產生簡體文字或大陸用語。")

    add_heading_3("【步驟三：結束說話並啟動辨識】")
    add_p("口述完畢後，再次輕按一下 [右側 Ctrl] 鍵。此時耳機會聽見沉穩的低頻「咚（750Hz）」提示音，浮動視窗立即切換為藍色流動進度光條，神經網路以毫秒速度進行特徵解碼、神經網絡標點斷句與同音修正。")
    add_image_box("assets/ref_images/image3.png", "圖 3-4：辨識中狀態——螢幕底部藍色流動進度光條（低頻提示音：咚 750Hz）", width_in=3.0)

    add_heading_3("【步驟四：極速自動打上螢幕】")
    add_p("辨識完成瞬間，浮動視窗切換為綠色打勾動畫並迅速淡出，整理完成的文字將以模擬人類鍵盤輸入的方式，精準填入游標所在的應用程式中！")
    add_image_box("assets/ref_images/image4.png", "圖 3-5：完成上屏狀態——螢幕底部綠色打勾動畫並淡出完成打字", width_in=3.0)

    # ==========================
    # 第四章 系統匣常駐圖示與右鍵功能選單全解
    # ==========================
    add_heading_1("第四章 系統匣常駐圖示與右鍵功能選單全解")
    add_p("軟體啟動後會常駐於 Windows 螢幕右下角工作列系統匣中，提供最直覺、最現代化的管理體驗。")

    add_image_box("assets/tray_icon_guide.png", "圖 4-1：Windows 系統匣與工作列圖示溢位區位置指引", width_in=5.4)

    add_heading_2("4.1 系統匣圖示狀態指示說明")
    add_p("系統匣小圓形圖示會依軟體當前生命週期即時變更圖樣與顏色：")
    add_p("• 🔵 藍色「FT」圖示：正常待命狀態，隨時可按熱鍵啟動語音打字。")
    add_p("• ⚪ 灰色「...」圖示：背景模型正在載入或預熱中（通常僅需 1~2 秒），請稍候片刻。")
    add_p("• 🔴 紅色「REC」圖示：正在錄音聆聽中，麥克風開啟。")
    add_p("• 🔴 紅色「ERR」圖示：模型載入發生異常，可點擊查看同目錄下之 app.log 排除問題。")

    add_heading_2("4.2 v3.3 簡化優化版系統匣右鍵選單")
    add_p("在右下角「FT」圖示上按『滑鼠右鍵』，即可展開功能完整的操作選單：")

    add_image_box("assets/v33_tray_menu.png", "圖 4-2：v3.3 系統匣完整右鍵選單與三大打字模式展開截圖", width_in=5.8)

    add_heading_3("右鍵選單各功能項目解析")
    add_p("1. 🟢 引擎狀態指示列：顯示「黃金引擎在線 (SenseVoice + CT標點 + Qwen-0.5B)」，點擊不會動作，作為核心神經網路健康狀態之即時指示。")
    add_p("2. 打字與段落重編模式 (Typing Mode) 子選單：")
    add_p("   • 🟢 極速打字模式 (Instant - 0ms免LLM・即時標點上屏)")
    add_p("   • 🟣 流暢修訂與同音精校 (Typeless - 0.5B極速修錯字/潤飾 - 預設推薦)")
    add_p("   • 🔵 結構化闡述與指令模式 (Structured - 長篇重組為條理重點)")
    add_p("   > 註：切換打字模式時，內嵌 0.5B 模型之 KV Cache 保持常駐不失效，無須重新加載模型權重，瞬間即時生效！")
    add_p("3. 快速鍵設定 (Hotkey) 子選單：")
    add_p("   • 右側 Ctrl (Right Ctrl - 推薦)")
    add_p("   • 右側 Alt (Right Alt)")
    add_p("   • F8 鍵")
    add_p("   • 開啟設定檔手動自訂...（可指定任意鍵盤按鍵）")
    add_p("4. 開機自動啟動 (Start on Boot)：點擊勾選即可一鍵開啟或關閉 Windows 開機隨系統啟動功能。")
    add_p("5. 自訂專有名詞與設定 (Config)：直接以 Windows 記事本開啟 config.json 設定檔，修改後存檔即時動態生效。")
    add_p("6. 結束程式 (Exit)：完全退出軟體背景常駐，釋放本機記憶體。")

    # ==========================
    # 第五章 專有名詞聲學校正與個人化設定
    # ==========================
    add_heading_1("第五章 專有名詞聲學校正與個人化設定 (config.json)")
    add_p("為了滿足各行各業（如半導體、軟體開發、醫療、法律、教育、金融）的專業術語需求，FunASRVoiceTyper_Turbo 內建 Layer 1.5 專有名詞聲學校正模組，並支援即時動態重載（Hot Reload）。")

    add_image_box("assets/v33_config_guide.png", "圖 5-1：config.json 設定檔架構與即時熱重載機制示意圖", width_in=5.8)

    add_heading_2("5.1 config.json 設定檔範例解析")
    add_p("在系統匣右鍵選單點選『自訂專有名詞與設定 (Config)』即可開啟 config.json。主要欄位設定如下：")

    add_callout(
        "⚙️ config.json 標準配置範例",
        [
            "{",
            '  "hotkey": "right ctrl",              // 全域開關式熱鍵，推薦 right ctrl / right alt / f8',
            '  "typing_mode": "typeless",           // 預設打字模式: instant / typeless / structured',
            '  "auto_start": true,                  // 開機是否隨 Windows 自動常駐運行',
            '  "domain_terms": [                    // 專業術語、科技名詞與別名映射詞庫',
            '    "台積電", "CoWoS", "EUV", "先進製程", "晶圓代工", "半導體",',
            '    "AI", "API", "Agent", "Meeting", "GitHub", "Windows", "Linux",',
            '    "城市=>程式",                       // 顯式別名映射：強制將「城市」修正為「程式」',
            '    "程試碼=>程式碼",                    // 同音錯字修正：將「程試碼」校正為「程式碼」',
            '    "測型檔案=>測試檔案",                 // 術語校正：將「測型檔案」校正為「測試檔案」',
            '    "治安=>資安",                        // 平捲舌錯字修正：將「治安」修正為「資安」',
            '    "大竹郭小=>大竹國小"                 // 人名或地名專有詞修正',
            '  ]',
            "}"
        ],
        border_color="0284C7",
        bg_color="F8FAFC"
    )

    add_heading_2("5.2 專有名詞與同音校正四大核心機制")
    add_p("1. 免重啟即時動態生效 (Hot Reload)：使用記事本修改 config.json 中的 domain_terms 詞彙後，只要按下 Ctrl+S 存檔，程式在下一次按下熱鍵錄音時便會動態讀取最新詞彙，完全不需要重新啟動應用程式！")
    add_p("2. 「錯字=>正字」顯式別名映射：若某些罕見專有名詞、自創品牌或縮寫發音差異較大，可使用「A=>B」語法（例如「扣窩斯=>CoWoS」或「層次碼=>程式碼」），系統會以最高優先權強制執行精準置換。")
    add_p("3. 英文大小寫自動正規化：將縮寫填入詞庫（如 CoWoS、EUV、API、GitHub），系統會自動將語音辨識輸出之純小寫文字矯正為正確的英文大小寫格式。")
    add_p("4. 台灣國語同音與模糊音包容：內建聲學校正模組，自動涵蓋台灣常見平捲舌混淆（z/zh、c/ch、s/sh）與前後鼻音（in/ing、en/eng）。當清單中包含「資安」時，語音辨識即使輸出同音的「治安」，系統也會自動智慧校準為「資安」。")

    # ==========================
    # 第六章 常見問題與排錯指南 (FAQ)
    # ==========================
    add_heading_1("第六章 常見問題與排錯指南 (FAQ)")

    add_heading_2("Q1：按了鍵盤右側 Ctrl 鍵，為什麼沒有聽見提示音，也沒有出現紅色麥克風？")
    add_p("• 原因一【模型剛啟動加載中】：程式初次啟動時，正在背景載入 SenseVoice-Small、CT-Transformer 與 Qwen2.5-0.5B 模型（約需 1~2 秒）。加載完成時會發出一聲短嗶聲確認，此後即可隨按隨用。若此時按鍵，系統會以一聲短低頻嗶聲提示「模型載入中」。")
    add_p("• 原因二【目標視窗權限較高】：若您將游標點在以「系統管理員身分 (Administrator)」執行的視窗中（例如工作管理員或防毒軟體設定視窗），普通權限的程式無法對其發送鍵盤事件。建議將游標點在一般應用程式（如 Word、LINE、瀏覽器）中再按熱鍵。")
    add_p("• 原因三【熱鍵被其他全螢幕遊戲或軟體獨佔攔截】：若其他軟體先註冊了全域熱鍵，您可在系統匣右鍵選單點選『快速鍵設定』，隨時改為『右側 Alt』或『F8 鍵』。")

    add_heading_2("Q2：三大打字模式 (Instant / Typeless / Structured)，在工作上該如何精準選擇？")
    add_p("• 【追求極限秒速】：選擇「Instant 極速打字模式」。完全跳過 LLM 處理階段，僅由 SenseVoice-Small + CT-Transformer 標點進行轉錄，50~100 毫秒秒速打上螢幕，適合 LINE 快速對話、程式碼註解。")
    add_p("• 【追求自然專業（強烈推薦）】：選擇「Typeless 流暢修訂模式」。0.5B 輕量大模型在 0.6 秒內自動過濾掉口語贅詞（例如「那個...就是...嗯...」），並將同音錯字修復，產出語意最流暢的正式書面文句，最適合公文、Email 與企劃案。")
    add_p("• 【追求整理與條理】：選擇「Structured 結構化闡述模式」。當您口述一段包含多個要點的長文時，系統會自動提煉出標題並分點條列（1. 2. 3.），最適合會議記錄整理與交辦清單。")

    add_heading_2("Q3：如果完全沒有網路連線（拔掉網線或飛航模式），軟體還能使用嗎？")
    add_p("• 答案是【完全不受影響，100% 正常運作】！")
    add_p("• 本軟體採用真正的「純本地端邊緣運算 (On-Device Inference)」，所有 ASR、標點、LLM 語意重構都在您本機的 CPU/RAM 上運算，完全不需要任何對外網路連線，實體隔離環境 (Air-Gap) 同樣秒出字，杜絕任何資安外洩風險。")

    add_heading_2("Q4：如果不需要開機自動啟動，該如何關閉？")
    add_p("• 直接在螢幕右下角系統匣圖示上按滑鼠右鍵，在選單中點擊『開機自動啟動 (Start on Boot)』，取消勾選即可解除 Windows 開機常駐。")

    add_heading_2("Q5：本機 CPU 運算會不會佔用大量記憶體或造成電腦卡頓？")
    add_p("• 本版本已徹底實施輕量化，將所有非必要的龐大模型全部移除，僅保留以下三大核心輕量模型：")
    add_p("  - SenseVoice-Small ONNX 旗艦語音模型（約 230 MB）")
    add_p("  - CT-Transformer 27萬詞表標點大模型（約 270 MB）")
    add_p("  - Qwen2.5-0.5B-Instruct 輕量語意精校模型（約 397 MB）")
    add_p("• 總記憶體佔用極低（常駐僅約 600MB ~ 700MB），推論時 CPU 負載瞬間即逝，即使是普通辦公筆電也能順暢無感運行，絲毫不影響日常其他軟體運作。")

    # 儲存手冊
    output_path = os.path.join(target_dir, "FunASRVoiceTyper_Turbo 操作手冊.docx")
    doc.save(output_path)
    print(f"Word 手冊生成成功: {output_path}")

    # 同步複製到 dist 發行目錄 (若存在)
    dist_dir = os.path.join(target_dir, "dist", "FunASRVoiceTyper_Turbo")
    if os.path.exists(dist_dir):
        dist_copy = os.path.join(dist_dir, "FunASRVoiceTyper_Turbo 操作手冊.docx")
        shutil.copy2(output_path, dist_copy)
        print(f"Word 手冊已同步複製至發行目錄: {dist_copy}")

if __name__ == '__main__':
    build_manual_docx()
