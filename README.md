# FunASRVoiceTyper Turbo v3.3 (黃金輕量專用版)
## 全域開關式・純本地極速語音打字系統

> **版本**：v3.3 Lean Golden Edition  
> **系統環境**：Windows 10 / Windows 11 (64-bit)  
> **預設熱鍵**：鍵盤 `Right Ctrl`（開關切換式 Toggle Mode，按一下說話、說完再按一下上屏）  
> **資安與隱私**：100% 本地離線推論（零對外網路連線・實體隔離 Air-Gap 正常運作）

---

### 📥 快速下載資源專區 (Quick Downloads)

本專案已完成輕量化整理，您可以直接在下方點擊下載所需資源：

| 下載項目 | 檔案格式 / 下載連結 | 說明 |
| :--- | :--- | :--- |
| **可以直接執行的安裝設定包** | [📦 **下載 FunASRVoiceTyper_Turbo_Installer.zip**](FunASRVoiceTyper_Turbo_Installer.zip) | 內含一鍵自動安裝精靈、常駐註冊、開機自動啟動與解除安裝腳本。 |
| **完整專案原始程式碼** | [💻 **下載 FunASRVoiceTyper_Turbo_SourceCode.zip**](FunASRVoiceTyper_Turbo_SourceCode.zip) | 內含完整 `core/`、`assets/`、主程式與建置規格，適合開發與二次封裝。 |
| **使用者操作手冊 (Word 版)** | [📄 **下載 FunASRVoiceTyper_Turbo 操作手冊.docx**](FunASRVoiceTyper_Turbo%20%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8A.docx) | 包含完整操作手冊排版與十餘張高清操作畫面截圖的 Word 說明文件。 |
| **線上操作手冊 (Markdown 版)** | [📖 **閱讀 線上操作說明書.md**](操作說明書.md) | 在 GitHub 線上直接瀏覽圖文並茂的操作手冊。 |
| **免安裝隨身版 (含完整模型)** | [🚀 **前往 GitHub Releases 下載 Portable.zip (約 1.1GB)**](https://github.com/Chery415/FunASRVoiceTyper_Turbo/releases/tag/v3.3.0) | 已預先編譯並內建 SenseVoice + CT標點 + Qwen2.5-0.5B 模型，解壓縮即可直接使用！ |

---

![實境打字展示](assets/v33_live_typing_showcase.png)

---

## 🌟 核心特色摘要

- **三大實用打字模式自由切換**：
  - **🟢 Instant 極速打字模式**：0ms 免 LLM，純語音 + CT 標點 + 聲學專名校正，50~150ms 秒出字，適合 LINE 快速對話。
  - **🟣 Typeless 流暢修訂與同音精校模式（推薦）**：0.5B 輕量語意大模型在 0.6 秒內自動過濾口語贅詞（那個、嗯、然後）並修復同音錯字（如程式碼、測試檔案）。
  - **🔵 Structured 結構化闡述模式**：口述長篇大論自動提煉為結構化標題與編號重點清單，適合會議記錄整理。
- **開關切換式操作 (Toggle Mode)**：按一下熱鍵叮一聲開始聆聽，說完再按一下咚一聲結束並自動上屏，**無須持續按住鍵盤**，雙手完全自由！
- **專有名詞聲學智慧修正**：內建 Layer 1.5 專有名詞聲學校正模組，支援「`錯字=>正字`」別名強制映射、科技英文大小寫自動正規化，並自動包容台灣國語平捲舌與前後鼻音差異。
- **100% 離線純本機推論**：零網路連線依賴、零音訊外部上傳，實體隔離拔網線 (Air-Gap) 依舊毫秒級運作，徹底保障個人隱私與企業機密資安！

---

## 🖥️ 系統匣右鍵選單與三大模式

![系統匣右鍵選單截圖](assets/v33_tray_menu.png)

![三大打字模式對比圖](assets/v33_modes_diagram.png)

---

## ⌨️ 開關式操作流程 (Toggle Mode)

![鍵盤熱鍵操作說明](assets/keyboard_hotkey.png)

![四步驟打字流程圖](assets/v33_typing_flow_steps.png)

1. **定位游標**：將游標點在任何需要輸入文字的視窗（如 Word、LINE、瀏覽器、記事本、VS Code）。
2. **啟動聆聽**：輕按一下鍵盤上的 **[右側 Ctrl]** 鍵，耳機聽見高頻提示音（叮 1000Hz），螢幕下方出現紅色脈動麥克風波形膠囊。
3. **自然說話**：以正常語速講話，支援中英混說、數字百分比自動正規化（如「80%」）。
4. **結束上屏**：說完後再輕按一下 **[右側 Ctrl]** 鍵，耳機聽見低頻提示音（咚 750Hz），神經網路即時完成辨識，文字如同真人打字般自動填入！

---

## ⚙️ 專有名詞自訂與熱重載 (config.json)

![config.json 設定與熱重載示意圖](assets/v33_config_guide.png)

在系統匣圖示按右鍵點擊『自訂專有名詞與設定 (Config)』，直接以記事本編輯 `config.json`：
- 支援「`錯字=>正字`」別名映射（例如：`城市=>程式`、`測型檔案=>測試檔案`、`大竹郭小=>大竹國小`）。
- 支援科技英文大小寫正名（例如：`CoWoS`、`EUV`、`API`、`AI`、`GitHub`）。
- 存檔 (Ctrl+S) 後**即時熱重載 (Hot Reload)**，下一次按熱鍵立即生效，無須重新啟動程式！

---

## 📄 授權條款 (License)
本專案採用 MIT 開源授權，歡迎自由修改與二次分發。
