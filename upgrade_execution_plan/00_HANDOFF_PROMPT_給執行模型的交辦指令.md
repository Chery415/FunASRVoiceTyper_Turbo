# 🚀 交辦給 Gemini 3.8 Flash 的一鍵啟動指令 (Handoff Prompt)

> **使用方式**：當您切換至 **Gemini 3.8 Flash** 模型後，只需將下方區塊內的文字直接複製貼上發送給它，它就會自動讀取本資料夾（`upgrade_execution_plan/`）內的所有規格文件並依序執行完畢。

---

## 📋 複製以下內容發送給 Gemini 3.8 Flash：

```text
請擔任資深 Python 系統與本地 AI 部署工程師，幫我執行 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo` 專案的「v3.0 全內嵌雙引擎升級計畫」。

我已經在專案目錄下的 `upgrade_execution_plan/` 資料夾中準備好了完整的規劃執行工作說明書。請你嚴格依照以下順序閱讀文件並逐步落地執行，不要省略任何步驟：

1. 先閱讀 `upgrade_execution_plan/01_MASTER_EXECUTION_SPEC_主執行工作說明書.md`，全面理解專案背景、硬體與企業資安限制（禁止依賴外部 Ollama、禁止開啟任何網路 Listening Port、100% 記憶體內 In-Process 推論、無須管理員權限），並執行 Phase 1（安裝套件與下載 CTranslate2 Whisper 模型及 GGUF 語言模型）。
2. 接著閱讀 `upgrade_execution_plan/02_CODE_MODIFICATION_GUIDE_程式碼完整改寫規格書.md`，嚴格按照規格書中的完整程式碼與介面契約，依序完成以下檔案的修改與升級：
   - `config.json`
   - `core/domain_normalizer.py`
   - `core/asr_engine.py`
   - `core/llm_client.py`
   - `core/prompt.py`
   - `core/pipeline.py`
   - `core/wave_overlay.py`
   - `main.py`
3. 最後閱讀 `upgrade_execution_plan/03_PACKAGING_AND_SECURITY_AUDIT_打包與資安檢驗規範.md`，建立並執行自動化驗證腳本 `test_upgrade_pipeline.py`，確認：
   - 第一階段 `faster-whisper` 聲學熱詞導引（Hotwords）與中英夾雜辨識正常運作。
   - 第二階段內嵌 `llama-cpp-python` (GGUF) 能夠針對口語停頓、贅字、重複與不順暢的語句進行整段重新編排、修訂與流暢闡述，且不再發生 1.5 秒超時降級。
   - 更新打包與資安稽核腳本，確認 `netstat` 零外部連線與零開放 Port，以及 Bandit SAST 掃描 0 高風險。

請現在開始讀取 `upgrade_execution_plan/01_MASTER_EXECUTION_SPEC_主執行工作說明書.md` 並開始執行！
```

---

## 📂 本資料夾文件結構索引

| 檔案名稱 | 用途說明 |
| :--- | :--- |
| [`00_HANDOFF_PROMPT_給執行模型的交辦指令.md`](./00_HANDOFF_PROMPT_給執行模型的交辦指令.md) | 本檔案，提供直接複製貼上給 Gemini 3.8 Flash 的交辦提示詞與任務總覽。 |
| [`01_MASTER_EXECUTION_SPEC_主執行工作說明書.md`](./01_MASTER_EXECUTION_SPEC_主執行工作說明書.md) | 定義痛點根因、企業資安紅線、目標架構、環境套件安裝指令與自動化模型下載腳本。 |
| [`02_CODE_MODIFICATION_GUIDE_程式碼完整改寫規格書.md`](./02_CODE_MODIFICATION_GUIDE_程式碼完整改寫規格書.md) | 提供每個核心模組（ASR、口語去重、內嵌 GGUF LLM、段落重編 Prompt、主程式 UI）的完整改寫程式碼與細節。 |
| [`03_PACKAGING_AND_SECURITY_AUDIT_打包與資安檢驗規範.md`](./03_PACKAGING_AND_SECURITY_AUDIT_打包與資安檢驗規範.md) | 提供端到端測試驗收腳本、PyInstaller 綠色免安裝打包更新，以及企業資安審查腳本同步指南。 |
