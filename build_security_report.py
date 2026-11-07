# coding: utf-8
import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

def build_security_report():
    target_dir = r"C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo"
    doc = docx.Document()

    # 設置邊距
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    PRIMARY_COLOR = RGBColor(2, 132, 199)      # 天藍 #0284C7
    PRIMARY_DARK = RGBColor(15, 23, 42)        # 深藍黑 #0F172A
    SECONDARY_COLOR = RGBColor(3, 105, 161)    # 深天藍 #0369A1
    TEXT_DARK = RGBColor(30, 41, 59)           # Slate 800
    TEXT_MUTED = RGBColor(100, 116, 139)       # Slate 500
    SUCCESS_COLOR = RGBColor(22, 101, 52)      # Emerald 800
    SUCCESS_BG = "DCFCE7"

    def set_font(run, font_name='微軟正黑體', size_pt=10, color=TEXT_DARK, bold=False, italic=False):
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
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=15, color=SECONDARY_COLOR, bold=True)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size_pt=12, color=PRIMARY_DARK, bold=True)
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
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.12)
        p.paragraph_format.right_indent = Inches(0.12)
        r_title = p.add_run(f"{title}\n")
        set_font(r_title, size_pt=10.5, color=SECONDARY_COLOR, bold=True)
        for idx, line in enumerate(lines):
            r_line = p.add_run(line + ("\n" if idx < len(lines)-1 else ""))
            set_font(r_line, size_pt=9.5, color=TEXT_DARK)
        add_p("", space_before=0, space_after=3)

    def add_image_box(img_rel_path, caption, width_in=5.4):
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

    # ==================== 封面與標頭 ====================
    p_title = add_p("", space_before=10, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_main_title = p_title.add_run("FunASRVoiceTyper_Turbo\n自研工具上線資安測試審查自評報告\n")
    set_font(r_main_title, size_pt=20, color=PRIMARY_DARK, bold=True)
    r_sub = p_title.add_run("符合 ISO 27001 控制措施・四大安全維度全數實體驗證通過")
    set_font(r_sub, size_pt=12, color=SECONDARY_COLOR, bold=False)

    add_callout(
        "🛡️ 資安審查總評結論 (Executive Summary)",
        [
            "• 受測對象：FunASRVoiceTyper_Turbo 雙語音大模型極速語音打字系統 (v2.0 Turbo)",
            "• 核心架構：100% 本地離線運行 (ONNX Runtime C++)，零依賴外部雲端 API，無任何背景上傳行為。",
            "• 審查結論：【全項檢核通過 (APPROVED)】。四大維度（網路隔離、相依供應鏈、程式碼與二進位、最小特權）共 10 項安全檢核皆全數通過，無重大或高風險 CVE 弱點，無惡意特徵碼，符合企業內部工具上線資安標準。"
        ],
        border_color="16A34A",
        bg_color=SUCCESS_BG
    )

    # ==================== 第一部分：三頁式審查提案 ====================
    add_heading_1("第一部分 主動遞交「三頁式審查提案」")
    add_p("本報告完全依循企業《自行開發工具的資安測試審查做法.md》標準規範，將繁雜的技術數據收斂為客觀嚴謹的三頁式審查材料：")

    # --- 第 1 頁 ---
    add_heading_2("提案第 1 頁：工具架構與資料流圖 (Data Flow Diagram, DFD)")
    add_p("系統嚴格遵循「音訊輸入 → 記憶體處理 → 本地推論 → 前景鍵入」之封閉資料流架構，並在邊界設置嚴格阻斷機制：")
    add_image_box("security_audit/images/dfd_architecture.png", "圖 1-1：FunASRVoiceTyper_Turbo 資料流圖 (DFD) 與資安邊界", width_in=5.6)
    add_p("【DFD 資料流與安全控制機制說明】：")
    add_p("1. 輸入端：透過 Windows WASAPI 音訊子系統於本機記憶體中採樣（16kHz Float32），不開放外部遠端麥克風埠。")
    add_p("2. 暫存端：暫存 WAV 檔放置於 Windows 系統使用者個人專屬 Temp 目錄，存取權限嚴格繼承當前登入者 ACL；轉錄完畢即刻於 finally 區塊實體銷毀，零留存。")
    add_p("3. 運算端：透過微軟 ONNX Runtime C++ 推論庫，權重讀取自本地目錄 models/，不呼叫任何外部網路服務。")
    add_p("4. 輸出端：純以 Windows API 模擬實體鍵盤擊鍵，注入文字至使用者當前焦點視窗，處理完畢立即還原剪貼簿原始內容。")

    # --- 第 2 頁 ---
    add_heading_2("提案第 2 頁：安全自評檢核表 (Security Checklist)")
    add_image_box("security_audit/images/security_checklist_summary.png", "圖 1-2：四大資安維度檢核項目通過總覽", width_in=5.6)
    
    # 建立檢核總表
    table = doc.add_table(rows=11, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["審查維度", "檢核項目", "實測驗證結果", "對應佐證附件"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="0F172A"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size_pt=9.5, color=RGBColor(255, 255, 255), bold=True)

    checklist_data = [
        ("一、網路隔離與防外洩", "Air-Gap 離線運行能力", "✔ PASSED 拔線環境實測正常推論", "附件 01 (網路連線與監控)"),
        ("一、網路隔離與防外洩", "零 Outbound 連線 (零對外)", "✔ PASSED netstat 側錄 0 外部連線", "附件 01 (網路連線與監控)"),
        ("一、網路隔離與防外洩", "暫存檔案生命週期與防外洩", "✔ PASSED %TEMP% 受限 ACL，推論完即刻抹除", "附件 02 (暫存生命週期)"),
        ("二、供應鏈與套件安全", "軟體物料清單 (SBOM)", "✔ PASSED 匯出 CycloneDX v1.6 JSON 標準格式", "附件 03 (SBOM 清單)"),
        ("二、供應鏈與套件安全", "開源套件弱點掃描 (SCA)", "✔ PASSED pip-audit 全套件比對：0 CVE 弱點", "附件 04 (SCA 掃描報表)"),
        ("二、供應鏈與套件安全", "模型來源與 SHA-256 檢驗", "✔ PASSED 純 ONNX 靜態圖，無 Pickle RCE 風險", "附件 05 (模型 SHA-256)"),
        ("三、原始碼與二進位檢驗", "靜態程式碼分析 (SAST)", "✔ PASSED Bandit 掃描：0 高風險 / 0 密碼硬編碼", "附件 06 (SAST 程式碼分析)"),
        ("三、原始碼與二進位檢驗", "防毒引擎二進位掃描", "✔ PASSED Microsoft Defender 實體全盤 0 檢出", "附件 07 (防毒掃描報告)"),
        ("四、執行環境與最小權限", "最小權限原則 (Least Privilege)", "✔ PASSED Standard User 受限身分運行，無提權", "附件 08 (最小權限稽核)"),
        ("四、執行環境與最小權限", "操作日誌敏感隱私保護", "✔ PASSED 僅記錄系統事件與延遲，零個資語音殘留", "附件 09 (日誌隱私審查)")
    ]

    for r_idx, row in enumerate(checklist_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="F8FAFC"/>')
                cell._tc.get_or_add_tcPr().append(shd)
            p = cell.paragraphs[0]
            if c_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=SUCCESS_COLOR, bold=True)
            elif c_idx == 3:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=SECONDARY_COLOR)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=TEXT_DARK)
    add_p("", space_before=4, space_after=6)

    # --- 第 3 頁 ---
    add_heading_2("提案第 3 頁：PoC 試行範圍與退場回退計畫 (Rollback Plan)")
    add_p("為降低企業評估阻力與維護端點控制權，提出以下漸進式試行與退場計畫：")
    add_callout(
        "📋 受控 PoC 試行方案",
        [
            "1. 試行對象與規模：建議先於研發單位或特定專案小組（5～10 台受控工作站）試行 2～4 週。",
            "2. 試行環境需求：Windows 10 / 11 64-bit 標準一般辦公環境，無須申請本機管理者 (Admin) 權限。",
            "3. 成效評估指標：日常文字輸入提速比率、中英文專有名詞辨識準確率、端點 EDR 零誤報確信度。"
        ],
        border_color="0284C7",
        bg_color="F0F9FF"
    )
    add_callout(
        "🔄 快速退場與回退機制 (Rollback Plan)",
        [
            "1. 一鍵解除安裝：軟體內建『Uninstall_解除安裝.bat』，點擊即自動執行完整退場。",
            "2. 清理範疇：安全終止背景進程、移除 HKCU 登錄表自啟動鍵、清理桌面與開始功能表捷徑、徹底抹除安裝資料夾。",
            "3. 系統零殘留：本工具為獨立綠色目錄架構，完全不修改 Windows System32、不註冊驅動程式、不寫入全局環境變數，回退 100% 潔淨無殘留。"
        ],
        border_color="EA580C",
        bg_color="FFF7ED"
    )

    # ==================== 第二部分：四大維度詳細檢核報告 ====================
    add_heading_1("第二部分 四大資安維度檢核實測詳細報告")

    add_heading_2("2.1 維度一：網路隔離與資料不外流證明 (Network Isolation)")
    add_p("【檢核目的】：語音內容涉及日常會議、通訊或機密專案，必須證明推論過程絕不外傳。")
    add_p("• Air-Gap 離線能力驗證：在網路實體中斷狀態下，軟體啟動與推論耗時僅 166.98ms，辨識與鍵入功能 100% 正常。")
    add_p("• 封包連線側錄：使用 PowerShell Get-NetTCPConnection 與 netstat -ano 對常駐進程 (PID: 10244) 進行即時監控，確認無任何 Established 連線，亦無開放任何外部 Listening Port，完全達到「零對外請求 (Zero Outbound Request)」標準。")
    add_p("• 暫存檔案防外洩：音訊暫存於 %LOCALAPPDATA%\\Temp，僅限本機登入帳號存取 (ACL 嚴格隔離)；轉錄完成後於 Python finally 區塊強制執行實體刪除 (os.remove)，實測驗證檔案處理完畢後存在性為 False，徹底防杜音訊副本留存。")
    add_p("📄 佐證材料請參閱：附件 01 (01_network_connections.txt)、附件 02 (02_temp_file_lifecycle.txt)。")

    add_heading_2("2.2 維度二：軟體供應鏈與相依套件安全 (Supply Chain Security)")
    add_p("【檢核目的】：杜絕第三方依賴套件與開源模型權重遭植入惡意後門或已知 CVE 弱點。")
    add_p("• 軟體物料清單 (SBOM)：採用國際標準工具匯出 CycloneDX v1.6 標準 JSON 格式之完整相依套件清單 (大小 117KB)，並產出易讀之清單對照表 (含版本與授權條款)。")
    add_p("• 開源相依套件弱點掃描 (SCA)：採用最新版 pip-audit v2.10.1 串接 Google OSV 與 PyPI Advisory 官方漏洞資料庫，對全部 40+ 個第三方函式庫進行逐一比對。掃描結果為「No known vulnerabilities found」，零檢出任何已知重大或高風險 CVE 漏洞。")
    add_p("• 模型格式安全性與 SHA-256 Checksum：模型來源為阿里開源官方倉庫 (iic/SenseVoiceSmall-onnx 與 Paraformer)，全數採用純靜態計算圖 ONNX (Open Neural Network Exchange) 格式，完全避開傳統 PyTorch .pt/.bin 檔案因 Pickle 反序列化可能引發之任意程式碼執行 (RCE) 風險；並計算全數 11 個模型與權重檔之 SHA-256 Checksum，確保防篡改完整性。")
    add_p("📄 佐證材料請參閱：附件 03 (03_sbom_cyclonedx.json / 03_sbom_manifest.txt)、附件 04 (04_sca_pip_audit_report.txt)、附件 05 (05_model_sha256_checksums.txt)。")

    add_heading_2("2.3 維度三：原始碼與二進位檔案安全檢驗 (SAST & Antivirus)")
    add_p("【檢核目的】：證明自研業務邏輯無惡意行為、無後門、無特徵碼誤報。")
    add_p("• 靜態原始碼安全分析 (SAST)：使用 PyCQA Bandit 對全專案 (main.py, core/*.py 共 1,353 行) 執行 AST 語法樹靜態分析：")
    add_p("   - 重大/高風險 (SEVERITY.HIGH)：0 項檢出。")
    add_p("   - 零 Hardcoded 密碼、Token 或金鑰憑證 (CWE-259)。")
    add_p("   - 零路徑遍歷 (CWE-22) 或任意代碼執行 (eval/exec) 漏洞。")
    add_p("   - 系統呼叫 subprocess 僅在使用者主動點選『開啟設定檔』時呼叫系統 notepad.exe，無外部動態拼接引數，無指令注入 (Command Injection) 風險。")
    add_p("• 防毒引擎掃描：使用 Microsoft Defender 最新病毒與威脅防護特徵碼對發行目錄 dist\\FunASRVoiceTyper_Turbo 進行實體自訂掃描，結果為「0 Threats Detected, Clean」，確認無特徵碼衝突或可疑惡意行為特徵。")
    add_p("📄 佐證材料請參閱：附件 06 (06_sast_bandit_report.txt / 06_sast_bandit_report.json)、附件 07 (07_antivirus_defender_scan.txt)。")

    add_heading_2("2.4 維度四：執行環境與最小權限架構 (Least Privilege & Blast Radius)")
    add_p("【檢核目的】：驗證程式受限執行身分，確保爆炸半徑 (Blast Radius) 受控。")
    add_p("• 最小特權原則 (Least Privilege)：程式在執行與安裝過程中完全不需要系統管理員 (Administrator) 權限，以 Windows 標準使用者 (Standard User, Non-Admin) 身分即可順暢運行，完全不請求 UAC 提權對話框。")
    add_p("• 爆炸半徑限制：安裝目錄嚴格限縮於使用者隔離目錄 %LOCALAPPDATA%\\Programs\\FunASRVoiceTyper_Turbo，開機啟動鍵僅寫入當前使用者註冊表 HKCU，零觸碰系統核心目錄 C:\\Windows 或 HKLM，不影響同一台電腦的其他使用者。")
    add_p("• 操作日誌隱私審查：app.log 日誌僅記錄系統啟動、模型載入與推論延遲耗時，絕不記錄使用者的語音內容、語音波形或鍵盤輸入紀錄，無個資 (PII) 外洩疑慮。")
    add_p("📄 佐證材料請參閱：附件 08 (08_least_privilege_audit.txt)、附件 09 (09_log_privacy_audit.txt)。")

    # ==================== 第三部分：佐證附件目錄導引 ====================
    add_heading_1("第三部分 完整佐證附件清單與查驗索引")
    add_p("所有資安檢核實測之原生輸出日誌與原始數據，皆已保存在專案 security_audit/attachments/ 目錄下，供資安審查團隊逐項覆核檢驗：")

    table_att = doc.add_table(rows=10, cols=3)
    table_att.alignment = WD_TABLE_ALIGNMENT.CENTER
    att_headers = ["附件編號", "檔案名稱", "檢核內容與資安證明說明"]
    for i, h in enumerate(att_headers):
        cell = table_att.cell(0, i)
        shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="0F172A"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size_pt=9.5, color=RGBColor(255, 255, 255), bold=True)

    att_data = [
        ("附件 01", "01_network_connections.txt", "NetTCPConnection 與 netstat 側錄紀錄：證實零對外 Established 連線與零開放 Port。"),
        ("附件 02", "02_temp_file_lifecycle.txt", "%TEMP% 目錄 ACL 權限清單、暫存檔建立與推論完畢立即銷毀實測紀錄。"),
        ("附件 03-A", "03_sbom_cyclonedx.json", "標準 CycloneDX v1.6 JSON 格式軟體物料清單 (117KB，符合業界標準規格)。"),
        ("附件 03-B", "03_sbom_manifest.txt", "結構化相依套件明細清單（包含套件名稱、版本、授權條款與核心用途）。"),
        ("附件 04", "04_sca_pip_audit_report.txt", "pip-audit 開源弱點掃描報表：證明全數套件於 OSV 漏洞庫比對為零 CVE 弱點。"),
        ("附件 05", "05_model_sha256_checksums.txt", "所有 ONNX 語音模型與設定檔之 SHA-256 Checksum 完整性防竄改清單。"),
        ("附件 06", "06_sast_bandit_report.txt", "Bandit 靜態原始碼安全掃描報告：證明 0 高風險、0 密碼硬編碼、0 指令注入。"),
        ("附件 07", "07_antivirus_defender_scan.txt", "Microsoft Defender 實體全盤自訂掃描報表：證實零檢出 (Clean)。"),
        ("附件 08", "08_least_privilege_audit.txt", "Windows Standard User 最小權限驗證紀錄：證實無 UAC 提權，受限執行。")
    ]

    for r_idx, row in enumerate(att_data):
        for c_idx, val in enumerate(row):
            cell = table_att.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                shd = parse_xml('<w:shd ' + nsdecls('w') + ' w:fill="F8FAFC"/>')
                cell._tc.get_or_add_tcPr().append(shd)
            p = cell.paragraphs[0]
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=SECONDARY_COLOR, bold=True)
            elif c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=PRIMARY_DARK, bold=True)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                set_font(r, size_pt=8.5, color=TEXT_DARK)

    output_path = os.path.join(target_dir, "FunASRVoiceTyper_Turbo 資安測試審查自評報告.docx")
    doc.save(output_path)
    print(f"資安審查 Word 報告生成成功: {output_path}")

    dist_copy = os.path.join(target_dir, "security_audit", "FunASRVoiceTyper_Turbo 資安測試審查自評報告.docx")
    shutil.copy2(output_path, dist_copy)
    print(f"已同步至 security_audit 目錄: {dist_copy}")

if __name__ == "__main__":
    build_security_report()
