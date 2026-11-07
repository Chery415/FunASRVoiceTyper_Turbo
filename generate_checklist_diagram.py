# coding: utf-8
import os
from PIL import Image, ImageDraw, ImageFont

def get_fonts():
    font_paths = ["C:/Windows/Fonts/msjhbd.ttc", "C:/Windows/Fonts/msjh.ttc"]
    font_title, font_box_title, font_box_desc, font_badge = None, None, None, None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 24)
                font_box_title = ImageFont.truetype(fp, 17)
                font_box_desc = ImageFont.truetype(fp, 13)
                font_badge = ImageFont.truetype(fp, 12)
                break
            except Exception:
                pass
    if not font_title:
        font_title = ImageFont.load_default()
        font_box_title = ImageFont.load_default()
        font_box_desc = ImageFont.load_default()
        font_badge = ImageFont.load_default()
    return font_title, font_box_title, font_box_desc, font_badge

def create_checklist_summary():
    w, h = 1200, 680
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    f_title, f_box_title, f_box_desc, f_badge = get_fonts()

    # Header
    draw.rectangle([(0, 0), (w, 75)], fill=(15, 23, 42))
    draw.text((40, 22), "FunASRVoiceTyper_Turbo 資安檢核四大維度審查通過總覽", fill=(255, 255, 255), font=f_title)
    draw.text((980, 28), "100% 檢驗通過 (PASSED)", fill=(34, 197, 94), font=f_badge)

    # 4 Quadrants
    quads = [
        {
            "rect": [(40, 100), (580, 360)],
            "title": "一、網路隔離與資料不外流證明",
            "badge": "[PASSED 零外洩]",
            "color": (2, 132, 199),
            "bg": (240, 249, 255),
            "items": [
                ("Air-Gap 離線運行能力", "實體驗證拔網線完全正常推論"),
                ("網路連線與 Outbound 監控", "netstat 側錄：零對外 IP 連線 (Zero Outbound)"),
                ("暫存檔案生命週期檢核", "%TEMP% 受限 ACL，處理完畢立即實體抹除"),
                ("對應佐證附件", "附件 01 (網路連線)、附件 02 (暫存銷毀)")
            ]
        },
        {
            "rect": [(620, 100), (1160, 360)],
            "title": "二、軟體供應鏈與相依套件安全",
            "badge": "[PASSED 零漏洞]",
            "color": (16, 185, 129),
            "bg": (240, 253, 244),
            "items": [
                ("軟體物料清單 (SBOM)", "匯出標準 CycloneDX v1.6 JSON 格式清單"),
                ("開源相依弱點掃描 (SCA)", "pip-audit 深度比對 OSV 庫：零 CVE 弱點檢出"),
                ("模型權重來源防竄改", "純 ONNX 靜態圖格式 (無 Pickle RCE 風險)"),
                ("對應佐證附件", "附件 03 (SBOM)、附件 04 (SCA)、附件 05 (SHA256)")
            ]
        },
        {
            "rect": [(40, 390), (580, 640)],
            "title": "三、原始碼與二進位檔案安全檢驗",
            "badge": "[PASSED 無後門]",
            "color": (139, 92, 246),
            "bg": (245, 243, 255),
            "items": [
                ("靜態程式碼分析 (SAST)", "Bandit AST 掃描：0 高風險 / 0 密碼硬編碼 / 0 注入"),
                ("指令呼叫安全性", "無動態 Shell 命令拼接，固定系統記事本路徑"),
                ("防毒與二進位特徵掃描", "Microsoft Defender 實體全盤掃描：零檢出 Clean"),
                ("對應佐證附件", "附件 06 (SAST 報告)、附件 07 (防毒掃描報告)")
            ]
        },
        {
            "rect": [(620, 390), (1160, 640)],
            "title": "四、執行環境與最小權限架構",
            "badge": "[PASSED 最小特權]",
            "color": (234, 88, 12),
            "bg": (255, 247, 237),
            "items": [
                ("最小權限原則 (Least Privilege)", "Standard User 一般受限身分運行，無 UAC 提權"),
                ("爆炸半徑限制 (Blast Radius)", "限定 %LOCALAPPDATA% 與 HKCU，零觸碰系統檔"),
                ("操作日誌個資與隱私保護", "僅記錄系統事件與延遲，零語音、零文字個資記錄"),
                ("對應佐證附件", "附件 08 (最小權限稽核)、附件 09 (日誌隱私審查)")
            ]
        }
    ]

    for q in quads:
        draw.rounded_rectangle(q["rect"], radius=10, fill=q["bg"], outline=q["color"], width=2)
        rx1, ry1 = q["rect"][0]
        draw.text((rx1 + 18, ry1 + 16), q["title"], fill=q["color"], font=f_box_title)
        draw.text((rx1 + 380, ry1 + 18), q["badge"], fill=(21, 128, 61), font=f_badge)
        draw.line([(rx1 + 18, ry1 + 48), (q["rect"][1][0] - 18, ry1 + 48)], fill=(203, 213, 225), width=1)
        for idx, (k, v) in enumerate(q["items"]):
            draw.text((rx1 + 20, ry1 + 62 + idx * 42), f"• {k}:", fill=(15, 23, 42), font=f_box_desc)
            draw.text((rx1 + 200, ry1 + 62 + idx * 42), v, fill=(71, 85, 105), font=f_box_desc)

    out_path = r"security_audit\images\security_checklist_summary.png"
    img.save(out_path)
    print("Security checklist diagram saved to:", out_path)

if __name__ == "__main__":
    create_checklist_summary()
