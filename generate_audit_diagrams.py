# coding: utf-8
import os
from PIL import Image, ImageDraw, ImageFont

def create_dfd_diagram():
    w, h = 1200, 680
    img = Image.new("RGB", (w, h), (248, 250, 252))  # Slate 50
    draw = ImageDraw.Draw(img)

    # 嘗試載入微軟正黑體
    font_title = None
    font_box_title = None
    font_box_desc = None
    font_badge = None
    
    font_paths = ["C:/Windows/Fonts/msjhbd.ttc", "C:/Windows/Fonts/msjh.ttc"]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 26)
                font_box_title = ImageFont.truetype(fp, 18)
                font_box_desc = ImageFont.truetype(fp, 14)
                font_badge = ImageFont.truetype(fp, 13)
                break
            except Exception:
                pass
    if not font_title:
        font_title = ImageFont.load_default()
        font_box_title = ImageFont.load_default()
        font_box_desc = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # 頂部標題列
    draw.rectangle([(0, 0), (w, 75)], fill=(15, 23, 42))  # Slate 900
    draw.text((40, 22), "FunASRVoiceTyper_Turbo 資料流圖 (DFD) 與資安防護邊界", fill=(255, 255, 255), font=font_title)
    draw.text((950, 28), "100% 本地隔離環境", fill=(56, 189, 248), font=font_badge)

    # 外網防護禁行警示框 (右側外網區域)
    draw.rounded_rectangle([(870, 110), (1150, 620)], radius=12, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
    draw.text((890, 130), "網際網路 / 雲端環境 (External)", fill=(185, 28, 28), font=font_box_title)
    draw.text((890, 165), "[嚴格阻斷邊界]", fill=(220, 38, 38), font=font_badge)
    
    cloud_items = [
        "❌ 零 Outbound 連線",
        "❌ 零音訊上傳外部 API",
        "❌ 零外部雲端遙測 (Telemetry)",
        "❌ 零雲端模型推論依賴",
        "❌ 零第三方廣告追蹤",
        "✔ 實體 Air-Gap 拔線仍正常運作"
    ]
    for idx, item in enumerate(cloud_items):
        draw.text((890, 220 + idx * 45), item, fill=(153, 27, 27), font=font_box_desc)

    # 內部資料流節點 (左側本地受限使用者區域)
    draw.rounded_rectangle([(40, 110), (830, 620)], radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.text((60, 130), "本機作業系統執行邊界 (Local Client - Standard User Privilege)", fill=(3, 105, 161), font=font_box_title)

    # Node 1: 麥克風音訊捕捉
    draw.rounded_rectangle([(70, 190), (380, 280)], radius=8, fill=(240, 249, 255), outline=(2, 132, 199), width=2)
    draw.text((85, 205), "1. 麥克風輸入 (Microphone)", fill=(3, 105, 161), font=font_box_title)
    draw.text((85, 235), "• Windows WASAPI 音訊捕捉\n• 記憶體即時採樣 (Float32 / 16kHz)", fill=(71, 85, 105), font=font_box_desc)

    # Node 2: 暫存檔與生命週期
    draw.rounded_rectangle([(70, 340), (380, 440)], radius=8, fill=(254, 242, 242), outline=(244, 63, 94), width=2)
    draw.text((85, 355), "2. 暫存 WAV 檔 (Temp Storage)", fill=(190, 18, 60), font=font_box_title)
    draw.text((85, 385), "• 路徑: %LOCALAPPDATA%\\Temp\n• 權限: 嚴格受限 ACL (僅本使用者)\n• 週期: 轉錄完畢 try/finally 立即刪除", fill=(71, 85, 105), font=font_box_desc)

    # Node 3: 本地 ONNX 語音引擎
    draw.rounded_rectangle([(460, 190), (800, 310)], radius=8, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
    draw.text((475, 205), "3. 本地 ASR 推論 (FunASR ONNX)", fill=(21, 128, 61), font=font_box_title)
    draw.text((475, 235), "• SenseVoice-Small / Paraformer\n• ONNX Runtime C++ 純靜態圖推論\n• 內建神經網絡標點 + 逆文本正規化\n• 延遲: 50~100ms (100% 離線運算)", fill=(71, 85, 105), font=font_box_desc)

    # Node 4: 文字鍵入注入
    draw.rounded_rectangle([(460, 370), (800, 470)], radius=8, fill=(245, 243, 255), outline=(139, 92, 246), width=2)
    draw.text((475, 385), "4. 前景軟體鍵入 (Text Injection)", fill=(109, 40, 217), font=font_box_title)
    draw.text((475, 415), "• 模擬實體鍵盤上屏打字\n• 輸入至目前焦點游標 (LINE, Word等)\n• 剪貼簿原內容立即恢復", fill=(71, 85, 105), font=font_box_desc)

    # 箭頭繪製
    def draw_arrow(start, end, label=""):
        draw.line([start, end], fill=(2, 132, 199), width=3)
        # 箭頭端點
        ex, ey = end
        if end[1] > start[1]: # 向下
            draw.polygon([(ex-6, ey-10), (ex+6, ey-10), (ex, ey)], fill=(2, 132, 199))
        elif end[0] > start[0]: # 向右
            draw.polygon([(ex-10, ey-6), (ex-10, ey+6), (ex, ey)], fill=(2, 132, 199))
        if label:
            mx, my = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
            draw.text((mx + 8, my - 10), label, fill=(100, 116, 139), font=font_badge)

    draw_arrow((225, 280), (225, 340), "寫入暫存")
    draw_arrow((380, 390), (460, 260), "讀取音訊")
    draw_arrow((630, 310), (630, 370), "轉錄完成")

    # 紅色阻斷牆箭頭指向外網
    draw.line([(800, 250), (870, 250)], fill=(239, 68, 68), width=3)
    draw.line([(835, 235), (835, 265)], fill=(239, 68, 68), width=5)
    draw.text((815, 215), "阻斷", fill=(239, 68, 68), font=font_badge)

    # 底部說明列
    draw.rounded_rectangle([(70, 520), (800, 595)], radius=6, fill=(241, 245, 249), outline=(226, 232, 240), width=1)
    draw.text((85, 532), "安全總結：音訊資料完全於本機單一使用者工作階段中封閉處理，處理完畢立即抹除，具備實體等級隔離能力。", fill=(51, 65, 85), font=font_box_desc)
    draw.text((85, 560), "執行權限：Standard User（一般受限使用者身分），不具備系統管理員權限，無提權漏洞危害。", fill=(100, 116, 139), font=font_badge)

    out_path = r"security_audit\images\dfd_architecture.png"
    img.save(out_path)
    print("DFD architecture diagram saved to:", out_path)

if __name__ == "__main__":
    create_dfd_diagram()
