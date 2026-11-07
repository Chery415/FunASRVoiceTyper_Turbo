# 給 Gemini 3.8 Flash 執行模型的交辦指令 (Handoff Prompt - v3.2 高準度語音與標點雙引擎升級版)

您可以直接複製以下虛線框內的完整提示詞，貼給 **Gemini 3.8 Flash** 模型來執行本次「v3.2 高準度 ASR 模型替換與獨立標點大模型補齊計畫」：

---

```text
請擔任資深 Python 語音 AI 系統架構與效能優化工程師，幫我執行 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo` 專案的「v3.2 高準度 ASR 模型替換與獨立標點引擎升級計畫」。

我已經在專案目錄下的 `asr_accuracy_and_speed_plan/` 資料夾中準備好了完整的問題診斷與執行工作說明書。請你嚴格依照以下順序閱讀文件並逐步落地執行，不要省略任何步驟：

1. 先閱讀 `asr_accuracy_and_speed_plan/01_ASR_UPGRADE_AND_PUNC_SPEC_語音與標點引擎升級架構規格書.md`，全面理解造成先前版本「漏標點、同音錯字（如：大竹郭小/辨試）、切換 Paraformer 失效、以及 Whisper-Turbo 固定耗時 14 秒」的四大根因，並執行 Phase 1：更新 `download_upgrade_models.py` 並下載三大真實模型權重：
   - 獨立中文標點大模型：`manyeyes/punc_ct-transformer_zh-cn-common-vocab272727-onnx` -> `models/punc_ct-transformer_zh-cn-common-vocab272727-onnx`（僅下載 INT8 `model_quant.onnx` 與設定檔）
   - 中文旗艦非自回歸模型：`manyeyes/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx` -> `models/paraformer-large-onnx`（僅下載 INT8 `model_quant.onnx` 與設定檔）
   - 高準度自回歸輕量語境模型：`Systran/faster-whisper-small` -> `models/faster-whisper-small`
2. 接著閱讀 `asr_accuracy_and_speed_plan/02_CODE_MODIFICATION_GUIDE_完整程式碼改寫規格書.md`，嚴格按照規格書中的完整程式碼，依序完成 `download_upgrade_models.py`、`config.json`、`core/domain_normalizer.py`、`core/asr_engine.py`、`core/prompt.py`、`core/pipeline.py`、`main.py` 與 `build_package.py` 的修改與升級（若遇到任何 `.bat` 批次檔修改，嚴格遵守 `GEMINI.md` 規範：必須使用 `\r\n` CRLF 換行與 100% 純 ASCII 字元）。
3. 最後閱讀 `asr_accuracy_and_speed_plan/03_VERIFICATION_AND_PACKAGE_驗收測試與打包規範.md`，建立並執行自動化驗收腳本 `test_v32_asr_and_punc.py`，確認：
   - `Paraformer-large` + `CT-Transformer` 獨立標點模型成功載入且能自動為無標點長句補上精準逗號與句號（耗時 ~0.6~1.2 秒）。
   - `Whisper-Small` (INT8) 成功載入，具備自回歸上下文理解且推論速度比舊版 `Whisper-Turbo` 快 5 倍以上。
   - `SenseVoice-Small` 亦自動掛載 `CT-Transformer` 標點模型，徹底解決無逗號問題。
   - 內嵌 LLM 預設採用高準度 `Qwen2.5-1.5B-Instruct` 並對所有句子（`min_llm_char_length: 2`）進行錯別字與標點精校。
   接著執行 `build_package.py` 重新打包，並執行資安稽核腳本確認 100% 通過。

請現在開始讀取 `asr_accuracy_and_speed_plan/01_ASR_UPGRADE_AND_PUNC_SPEC_語音與標點引擎升級架構規格書.md` 並開始執行！
```
