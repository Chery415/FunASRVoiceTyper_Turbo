# 給 Gemini 3.8 Flash 執行模型的交辦指令 (Handoff Prompt - v3.1 極速流暢優化版)

您可以直接複製以下虛線框內的完整提示詞，貼給 **Gemini 3.8 Flash** 模型來執行本次「v3.1 極速流暢優化計畫」：

---

```text
請擔任資深 Python 系統效能調校與本地 AI 推論優化工程師，幫我執行 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo` 專案的「v3.1 極速流暢優化計畫 (Speed & Latency Optimization Plan)」。

我已經在專案目錄下的 `speed_optimization_plan/` 資料夾中準備好了完整的問題診斷與執行工作說明書。請你嚴格依照以下順序閱讀文件並逐步落地執行，不要省略任何步驟：

1. 先閱讀 `speed_optimization_plan/01_SPEED_BOTTLENECK_AND_ARCHITECTURE_速度瓶頸診斷與極速架構規格書.md`，全面理解造成 v3.0 辨識與切換模式緩慢的五大核心瓶頸（Whisper 熱詞重複鬼打牆迴圈、1069 tokens 肥大 System Prompt 導致切換模式時 KV Cache 100% 失效重算、i5-1135G7 四核心 Hyperthreading 執行緒搶占、Instant 模式與短句不必要呼叫 LLM、以及模型規模），並執行 Phase 1（更新 `download_upgrade_models.py` 並下載極速版 `qwen2.5-0.5b-instruct-q4_k_m.gguf` 模型）。
2. 接著閱讀 `speed_optimization_plan/02_CODE_MODIFICATION_GUIDE_極速化程式碼完整改寫規格書.md`，嚴格按照規格書中的完整程式碼，依序完成 `download_upgrade_models.py`、`config.json`、`core/asr_engine.py`、`core/prompt.py`、`core/llm_client.py`、`core/pipeline.py` 與 `main.py` 的修改與升級（若遇到任何 `.bat` 批次檔修改，嚴格遵守 `GEMINI.md` 規範：必須使用 `\r\n` CRLF 換行與 100% 純 ASCII 字元）。
3. 最後閱讀 `speed_optimization_plan/03_VERIFICATION_AND_BENCHMARK_極速驗收與效能基準測試規範.md`，建立並執行自動化效能基準測試與驗收腳本 `test_speed_optimization.py`，確認各項延遲指標（Instant 模式 LLM 0ms、短句極速通道、模式切換零快取失效、長段落重編速度提升 5~15 倍、Whisper 防鬼打牆）全數通過，接著執行 `build_package.py` 重新打包，並執行 `audit_step1_static.py`、`audit_step2_network.py`、`audit_step3_privileges.py` 確認 100% 通過企業資安審查。

請現在開始讀取 `speed_optimization_plan/01_SPEED_BOTTLENECK_AND_ARCHITECTURE_速度瓶頸診斷與極速架構規格書.md` 並開始執行！
```
