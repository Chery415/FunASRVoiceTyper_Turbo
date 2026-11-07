# coding: utf-8
import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

def build_docx():
    target_dir = r"C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo"
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        section.different_first_page_header_footer = False

    PRIMARY_COLOR = RGBColor(2, 132, 199)      # 天藍 #0284C7
    PRIMARY_DARK = RGBColor(3, 105, 161)       # 深藍 #0369A1
    TEXT_DARK = RGBColor(15, 23, 42)           # 深灰黑 #0F172A
    TEXT_MUTED = RGBColor(100, 116, 139)       # 灰 #64748B
    ACCENT_GREEN = RGBColor(16, 185, 129)      # 綠 #10B981
    ACCENT_RED = RGBColor(239, 68, 68)         # 紅 #EF4444

    def set_font(run, font_name='微軟正黑體', size_pt=10.5, color=TEXT_DARK, bold=False, italic=False):
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(size_pt)
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.italic = italic

    def add_p(text="", space_before=0, space_after=6, align=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.15):
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
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=15, color=PRIMARY_DARK, bold=True)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=12.5, color=TEXT_DARK, bold=True)
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
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Inches(0.12)
        p.paragraph_format.right_indent = Inches(0.12)
        r_title = p.add_run(f"{title}\n")
        set_font(r_title, size_pt=11, color=PRIMARY_DARK, bold=True)
        for idx, line in enumerate(lines):
            r_line = p.add_run(line + ("\n" if idx < len(lines)-1 else ""))
            set_font(r_line, size_pt=10, color=TEXT_DARK)
        add_p("", space_before=0, space_after=4)

    def add_image_box(img_rel_path, caption, width_in=5.2):
        img_path = os.path.join(target_dir, img_rel_path)
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.add_run().add_picture(img_path, width=Inches(width_in))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(0)
            p_cap.paragraph_format.space_after = Pt(8)
            r_cap = p_cap.add_run(f"▲ {caption}")
            set_font(r_cap, size_pt=9, color=TEXT_MUTED, italic=True)

    # 封面與標題
    p_title = add_p("", space_before=14, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_main_title = p_title.add_run("FunASRVoiceTyper Turbo 語音打字系統\n")
    set_font(r_main_title, size_pt=22, color=PRIMARY_DARK, bold=True)
    r_sub_title = p_title.add_run("雙語音大模型即時熱切換・純本機極速推論・全域打字操作手冊")
    set_font(r_sub_title, size_pt=13, color=TEXT_MUTED, bold=False)

    add_callout(
        "🌟 核心特色摘要",
        [
            "• 雙語音大模型自由切換：支援阿里最新旗艦 SenseVoice-Small (超低延遲/繁體優化) 與 Paraformer-large (穩健抗噪/會議長句) 雙引擎隨選即用。",
            "• 純本機離線極速推論：100% 離線運作，本體僅約 35MB 輕量封裝，自帶神經網絡標點斷句與逆文本正規化 (ITN)，辨識延遲僅 50~100ms，無須依賴外部大模型！",
            "• 開關切換式操作 (Toggle Mode)：按一下右側 Ctrl 叮一聲開始聆聽，說完再按一下咚一聲結束並自動上屏，無須持續按住長按！",
            "• 開機自動常駐系統匣：一鍵自動化安裝，開機秒進背景常駐，100% 離線隱私保障，語音與文字絕不離開本機。"
        ]
    )

    # 第 1 章 系統架構與模型對比
    add_heading_1("第一章 雙語音模型架構與規格解析")
    add_p("FunASRVoiceTyper_Turbo 採用阿里開源之頂尖非自回歸語音識別技術，提供兩大旗艦模型引擎，使用者可在系統匣選單中依使用情境即時切換：")

    table = doc.add_table(rows=6, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["比較項目", "SenseVoice-Small (預設推薦)", "Paraformer-large (長句會議)"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="0284C7"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size_pt=10, color=RGBColor(255, 255, 255), bold=True)

    rows_data = [
        ("模型發布年代", "2024 年全新開源架構", "成熟穩定非自回歸模型"),
        ("推論延遲", "極低延遲 (<70ms)，極速上屏", "標準延遲 (<150ms)"),
        ("標點與數字正規化", "內建豐富富文本標點、自動數字轉換 (ITN)", "搭配 CT-Transformer 神經網絡標點"),
        ("繁體與中英夾雜", "優異，完美支援台灣慣用語與科技中英混雜", "穩健，適合大段標準普通話長句"),
        ("推薦適用情境", "日常即時對話、LINE/Slack 聊天、程式碼寫作、短句郵件", "正式會議逐字稿、長篇訪談錄音、學術演講")
    ]
    for r_idx, row in enumerate(rows_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="F8FAFC"/>')
                cell._tc.get_or_add_tcPr().append(shd)
            p = cell.paragraphs[0]
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                set_font(r, size_pt=9.5, color=PRIMARY_DARK, bold=True)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=9.5, color=TEXT_DARK)
    add_p("", space_before=4, space_after=6)

    # 第 2 章 快速安裝與常駐配置
    add_heading_1("第二章 快速安裝與開機自動常駐")
    add_p("本系統提供免安裝 Python 環境的綠色目錄封裝，解壓縮後即可一鍵自動化安裝。")
    add_heading_2("2.1 一鍵自動安裝步驟")
    add_p("1. 進入程式目錄（或解壓縮後的 FunASRVoiceTyper_Turbo 資料夾）。")
    add_p("2. 對著「Setup_安裝與開機啟動.bat」按滑鼠右鍵選擇『以系統管理員身分執行』或直接按兩下滑鼠左鍵啟動。")
    add_p("3. 安裝精靈將自動執行以下動作：")
    add_p("   • 自動關閉舊版本程序，並將完整程式與 ONNX 模型部署至 Windows 使用者程式目錄：%LOCALAPPDATA%\\Programs\\FunASRVoiceTyper_Turbo。")
    add_p("   • 在 Windows 註冊表登錄開機常駐項目 (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)，確保每次開機自動在背景運行。")
    add_p("   • 自動在桌面與開始功能表建立「FunASRVoiceTyper Turbo」快捷方式。")
    add_p("   • 自動在背景啟動程式，並在右下角工作列系統匣顯示常駐圖示。")

    add_heading_2("2.2 完整解除安裝程序")
    add_p("若欲從電腦中完全移除本系統，只需在目錄中點擊「Uninstall_解除安裝.bat」即可。解除安裝精靈將安全關閉背景進程、移除開機註冊表項目、清理桌面與開始功能表捷徑，並完全刪除安裝目錄，不留下任何殘餘檔案。")

    # 第 3 章 核心操作規範
    add_heading_1("第三章 語音打字核心操作規範 (開關式 Toggle Mode)")
    
    add_callout(
        "⚠️ 操作方式特別說明 (請務必注意)",
        [
            "本軟體採用【開關切換式 (Toggle Mode)】操作機制，絕對【不是】長按熱鍵不放！",
            "✔ 正確操作：按一下熱鍵開始說話，說完再按一下熱鍵結束。手部在說話過程中完全自由，無須施力按壓鍵盤。",
            "✘ 錯誤操作：按住熱鍵不放講話、說完才放開。這會造成按鍵重複觸發判定，導致錄音提早中斷。"
        ],
        border_color="EF4444",
        bg_color="FEF2F2"
    )

    add_image_box("assets/keyboard_hotkey.png", "圖 3-1：鍵盤右側 Ctrl 鍵位置與開關式 (Toggle Mode) 操作邏輯", width_in=5.4)

    add_heading_2("3.1 四步驟標準打字流程")
    add_p("【步驟一：啟動聆聽】", space_before=4, space_after=2)
    add_p("將文字輸入游標點在任何您想輸入文字的軟體上（例如：Word、LINE、Teams、瀏覽器、記事本等）。輕輕按一下鍵盤上的 [右側 Ctrl] 鍵（Right Ctrl）。此時耳機會聽見清脆的高頻「叮（1000Hz）」提示音，螢幕正下方將浮現紅色脈動麥克風聲波動畫。")
    add_image_box("assets/ref_images/image2.png", "圖 3-2：聆聽中狀態——紅色脈動麥克風聲波（提示音：叮 1000Hz）", width_in=2.6)

    add_p("【步驟二：自然清晰說話】", space_before=4, space_after=2)
    add_p("以正常的語速與音量對麥克風說話。系統支援中英文混雜（例如：「這份 API 的 Response 已經由 TSMC 工程師 Review 通過」），且會自動為您添加標點符號與數字百分比（例如：「產能利用率提高到 80%」）。")

    add_p("【步驟三：結束聆聽並開始辨識】", space_before=4, space_after=2)
    add_p("語音講完後，緊接著再按一下 [右側 Ctrl] 鍵。此時耳機會聽見沉穩的低頻「咚（750Hz）」提示音，浮動視窗立刻切換為深藍色流動進度光條，系統正以毫秒級速度執行非自回歸 ASR 特徵解碼、智能標點斷句與逆文本正規化。")
    add_image_box("assets/ref_images/image3.png", "圖 3-3：辨識處理中狀態——藍色進度條（提示音：咚 750Hz）", width_in=2.6)

    add_p("【步驟四：文字極速自動打上螢幕】", space_before=4, space_after=2)
    add_p("辨識完成後，浮動視窗轉為綠色打勾動畫並迅速淡出，轉換後的文字將如同真人打字般，自動、完整地填入您游標所在的視窗軟體中！")
    add_image_box("assets/ref_images/image4.png", "圖 3-4：辨識完成上屏——綠色打勾提示", width_in=2.6)

    # 第 4 章 雙模型即時熱切換
    add_heading_1("第四章 雙語音模型即時熱切換功能")
    add_p("FunASRVoiceTyper_Turbo 首創系統匣即時熱切換技術。無論您目前在進行何種工作，都能隨時切換最適合的語音引擎：")
    add_p("1. 移動滑鼠至螢幕右下角工作列系統匣，找到『FT』藍色圓形圖示。")
    add_p("2. 在圖示上點擊『滑鼠右鍵』，展開功能選單。")
    add_p("3. 移動至『語音模型切換 (ASR Model)』子選單：")
    add_p("   • 點選【SenseVoice-Small (2024最新・高精準)】：切換至阿里面向富文本多語音模型，響應極速，繁體台灣慣用詞轉換最為自然。")
    add_p("   • 點選【Paraformer-large (經典穩健・會議轉錄)】：切換至阿里成熟非自回歸大模型，搭配 CT-Transformer 神經網絡斷句，適合嘈雜環境與超長句子。")
    add_p("4. 點選後系統會發出雙音提示音確認切換，系統匣圖示浮動資訊與右鍵選單單選圓點立即同步更新，無須重新啟動軟體！")

    # 第 5 章 系統匣功能與右鍵選單
    add_heading_1("第五章 系統匣常駐圖示與右鍵選單功能全解")
    add_image_box("assets/tray_icon_guide.png", "圖 5-1：Windows 工作列右下角系統匣與溢位區圖示指引", width_in=5.4)
    add_image_box("assets/ref_images/image5.png", "圖 5-2：系統匣滑鼠右鍵選單各功能實體截圖", width_in=3.6)

    add_heading_2("5.1 系統匣右鍵選單功能一覽")
    add_p("• LLM 校正狀態指示（選配進階擴充）：")
    add_p("   - 系統核心打字功能 100% 由本地語音模型（SenseVoice-Small / Paraformer-large）獨立極速運作，軟體預設【無須且未內建】額外的龐大 LLM 模型（如 Qwen2.5-3B）。")
    add_p("   - 系統匣選單預設顯示『⚪ 離線 (本地標點+ITN模式)』為標準正常狀態，文字轉錄、標點與繁體慣用字校正完全不受影響。")
    add_p("   - （選配）若進階使用者本機已自行安裝並常駐運行 Ollama (Qwen2.5-3B)，系統會自動偵測並切換至『🟢 在線』，提供額外的語意潤飾；若無則自動維持純語音模型的極速秒出字模式。")
    add_p("• 語音模型切換 (ASR Model)：即時切換 SenseVoice-Small 或 Paraformer-large 雙模型。")
    add_p("• 快速鍵設定 (Hotkey)：支援直接更換熱鍵為『右側 Ctrl (推薦)』、『右側 Alt』、『F8 鍵』或點擊『開啟設定檔手動自訂』。")
    add_p("• 開機自動啟動 (Start on Boot)：點擊勾選即可開啟或關閉 Windows 開機隨系統啟動功能。")
    add_p("• 自訂專有名詞與設定 (Config)：直接以記事本開啟 config.json。")
    add_p("• 結束程式 (Exit)：完全退出軟體背景常駐。")

    # 第 6 章 專有名詞自訂與進階設定
    add_heading_1("第六章 個人化設定檔 (config.json) 說明")
    add_p("系統中的 config.json 允許使用者依個人喜好自訂熱鍵、預設語音引擎與自訂專有名詞/別名替換。")
    add_p("本軟體具備【即時熱重載 (Hot Reload)】功能：直接以記事本編輯存檔後，下次按下熱鍵立即套用，無須重啟應用程式！")
    
    add_p("【config.json 欄位說明】：")
    add_callout(
        "⚙️ config.json 設定檔範本",
        [
            "{",
            '  "hotkey": "right ctrl",             // 全域開關熱鍵，推薦右側 Ctrl',
            '  "asr_model_id": "Paraformer-large",  // 預設 ASR 模型 (SenseVoice-Small / Paraformer-large)',
            '  "auto_start": true,                   // 開機是否自動啟動常駐',
            '  "enable_correction": true,            // 進階選配：若本機有 Ollama 時是否啟用外部輔助校正',
            '  "llm_timeout_seconds": 0.8,           // LLM 超時防護閾值 (秒)，超時自動降級回退',
            '  "domain_terms": [                     // 產業專有名詞與同音字替換清單',
            '    "台積電", "CoWoS", "EUV", "先進製程", "晶圓代工",',
            '    "半導體", "AI", "API", "Meeting",',
            '    "程式", "資安長", "資安",',
            '    "城市=>程式",                      // 支援「錯字=>正字」顯式別名映射',
            '    "治安=>資安"                       // 支援「同音錯字=>正確專有名詞」',
            "  ]",
            "}"
        ],
        border_color="0284C7",
        bg_color="F8FAFC"
    )

    add_heading_2("專有名詞與同音字智慧校正特色")
    add_p("1. 本機 100% 離線生效：內建 DomainTermsNormalizer 聲學校正模組，不依賴任何外部伺服器或大型語言模型，毫秒級完成修正。")
    add_p("2. 同音字與模糊拼音自動校正：納入台灣國語發音習慣（平捲舌音 zh/z, ch/c, sh/s、前後鼻音 in/ing, en/eng）。當您在 domain_terms 中加入「程式」或「資安」，系統辨識出同音的「城市」或「治安」時，會自動智慧替換為正確的專有名詞！")
    add_p("3. 顯式對照語法 (Alias Mapping)：若特定詞彙發音差異較大或為自訂簡稱，可使用「錯字=>正字」（例如「城市=>程式」、「扣窩斯=>CoWoS」），系統會以最高優先權進行替換。")
    add_p("4. 英文大小寫自動正名：輸入如「CoWoS」、「EUV」、「API」等專有名詞，系統會自動將語音轉出的 cowos、api 等自動正規化為正確的大小寫格式。")

    # 第 7 章 常見問題與排除
    add_heading_1("第七章 常見問題與排錯指南 (FAQ)")
    add_heading_2("Q1：按了熱鍵卻聽不到提示音，也沒有跳出浮動視窗？")
    add_p("• 原因一：程式剛啟動時正在背景非同步加載語音模型權重（約需 1~3 秒）。加載完成時會有一聲短嗶聲，此後即可隨按隨用。")
    add_p("• 原因二：系統匣圖示是否正常顯示『FT』？如果圖示為灰色『...』表示模型正在加載，若為紅色『ERR』請查看同目錄下的 app.log 日誌檔。")
    add_p("• 原因三：以最高系統管理員權限運行的軟體（如特定的防毒軟體或工作管理員視窗），普通權限程式無法直接模擬打字，建議以管理員身分運行或將游標點在一般視窗中。")

    add_heading_2("Q2：SenseVoice-Small 與 Paraformer-large 我該如何選擇？")
    add_p("• 平時打字（聊天、發信、寫程式備註）：強烈建議使用預設的【SenseVoice-Small】。延遲極低、語感自然、標點符號與台灣慣用字處理非常精準。")
    add_p("• 長篇會議或環境吵雜：建議切換至【Paraformer-large】。模型參數量大，抗噪能力極佳，長句識別極為平穩。")

    add_heading_2("Q3：如果我不希望開機自動常駐，該如何關閉？")
    add_p("直接在右下角系統匣圖示上按滑鼠右鍵，在選單中點擊『開機自動啟動 (Start on Boot)』，取消勾選即可。")

    add_heading_2("Q4：設定了專有名詞，如何確認它有正確生效？")
    add_p("只要在系統匣選單點擊『自訂專有名詞與設定 (Config)』，在 domain_terms 中填入您要的專有名詞（例如「程式」、「資安」），在記事本中按 Ctrl+S 存檔。下一次按下熱鍵錄音時，系統會立即動態讀取新設定，並將語音同音錯字（如「城市」、「治安」）自動替換為正確用字！")

    output_path = os.path.join(target_dir, "FunASRVoiceTyper_Turbo 操作手冊.docx")
    doc.save(output_path)
    print(f"Word 手冊生成成功: {output_path}")

    dist_copy = os.path.join(target_dir, "dist", "FunASRVoiceTyper_Turbo", "FunASRVoiceTyper_Turbo 操作手冊.docx")
    if os.path.exists(os.path.dirname(dist_copy)):
        shutil.copy2(output_path, dist_copy)
        print(f"Word 手冊已複製至發行目錄: {dist_copy}")

if __name__ == '__main__':
    build_docx()
