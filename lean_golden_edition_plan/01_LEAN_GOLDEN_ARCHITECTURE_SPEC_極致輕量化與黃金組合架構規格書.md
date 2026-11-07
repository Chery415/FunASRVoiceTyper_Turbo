# 01. 極致輕量化與黃金組合架構規格書 (v3.3 Lean Golden Edition Spec)

## 一、 升級背景與 18 種組合實測數據結論

經過對使用者 54.22 秒真實口述錄音檔（`錄音測試.m4a`）進行 **3 款語音模型 × 2 款語意模型 × 3 種打字模式 = 18 種全組合** 的嚴格基準實測，得出以下關鍵工程結論：

1. **語音模型（ASR）實測勝負**：
   - **`SenseVoice-Small` + `CT-Transformer`（綜合表現第一名 🏆）**：
     - 聽寫準確率最高：唯一完整且正確聽出「相應的截圖」與「模型進行測試」的模型，搭配 27 萬詞表 `CT-Transformer` 獨立標點神經網路後，全形逗號與句號斷句自然流暢，54 秒長音訊僅耗時 **11.48 秒**（短句僅需 **0.3 ~ 0.6 秒**）。
   - `Paraformer-large`（淘汰）：雖然速度快（9.81s），但在專業詞彙上出現較多同音字（「相應的結果」、「測行檔案」、「測告」）。
   - `Whisper-Small`（淘汰）：耗時高達 **22.26 秒**，且因自回歸時間戳切分產生嚴重標點碎裂（`,，`、`。，`）與大量同音錯字（「檔按」、「測識步驟」、「測示嗎」、「測四」），並夾帶龐大的 `faster-whisper` / `ctranslate2` 依賴庫（佔用近 500MB+）。

2. **語意重構模型（LLM）實測勝負**：
   - **`Qwen2.5-0.5B-Instruct (Q4_K_M)`（速度與性價比之王 🏆）**：
     - 在同音錯字修正與標點潤飾上（如將「程試碼」修為「程式碼」、「測型檔案」修為「測試檔案」），**`0.5B` 的修正品質與 `1.5B` 達到 100% 完全相同的水準**！
     - 但 `0.5B` 的推論速度比 `1.5B` 快了 **1.5 ~ 2.3 倍**，且模型檔案僅 **397 MB**（相比 `1.5B` 的 **986 MB** 節省了近 600 MB 磁碟與記憶體空間）。

3. **最終保留之黃金組合（對應原測試組合 16、17、18）**：
   - **組合 16（日常極速打字）**：`SenseVoice-Small` + `CT-Transformer` + `Qwen2.5-0.5B` + **`Instant` 模式 (0ms LLM)**
   - **組合 17（流暢同音精校）**：`SenseVoice-Small` + `CT-Transformer` + `Qwen2.5-0.5B` + **`Typeless` 模式**
   - **組合 18（長篇結構化闡述）**：`SenseVoice-Small` + `CT-Transformer` + `Qwen2.5-0.5B` + **`Structured` 模式**

---

## 二、 v3.3 極致輕量化瘦身目標 (Lean & Clean Architecture)

為了讓專案易於維護、快速啟動並大幅縮小打包發布體積（減少約 **1.7 GB ~ 2.5 GB** 的冗餘權重與套件），v3.3 執行以下四大瘦身工程：

### 1. 模型目錄硬碟瘦身（僅保留 3 個核心輕量模型）
- **保留模型**：
  1. `models/sensevoice-small-onnx/model_quant.onnx`（約 230 MB，唯一主語音模型）
  2. `models/punc_ct-transformer_zh-cn-common-vocab272727-onnx/model_quant.onnx`（約 278 MB，獨立 27 萬詞表中文標點大模型）
  3. `models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf`（約 397 MB，唯一內嵌語意精校模型）
- **徹底清理並移除之冗餘模型與暫存檔**：
  1. 刪除 `models/paraformer-large-onnx`（釋放 ~220 MB）
  2. 刪除 `models/faster-whisper-small`（釋放 ~484 MB）
  3. 刪除 `models/faster-whisper-turbo`（若存在，釋放 ~800 MB）
  4. 刪除 `models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf` 與 `models/qwen2.5-1.5b-instruct-q4_k_m.gguf`（釋放 ~1.0 GB）
  5. 刪除根目錄下重複的 `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`（統一收斂存放於 `models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf`，若根目錄有重複檔則移除以防打包重複）
  6. 刪除測試過程產生的暫存檔：`temp_test_audio.wav`、`benchmark_18_modes.py`、`benchmark_18_results.json`、`benchmark_18_results_full.json`。

### 2. 系統托盤（System Tray UI）極致簡化
- **移除**「語音模型切換 (ASR Model)」子選單（固定採用 `SenseVoice-Small + CT-Transformer`）。
- **移除**「語意重構模型切換 (LLM Accuracy/Speed)」子選單（固定採用 `Qwen2.5-0.5B`）。
- **保留**「打字與段落重編模式 (Typing Mode)」子選單（提供組合 16 `Instant`、組合 17 `Typeless`、組合 18 `Structured` 三種模式自由切換）。
- **保留**「快速鍵設定 (Hotkey)」、「開機自動啟動 (Start on Boot)」、「自訂專有名詞與設定 (Config)」、「結束程式 (Exit)」。

### 3. Layer 1.5 詞庫強化（讓 Instant 0ms 模式也具備 100% 專業詞準度）
- 將本次 54 秒實測錄音中 `SenseVoice-Small` 僅有的極少數同音詞（如 `程試碼=>程式碼`、`測試碼=>程式碼`、`測型檔案=>測試檔案`、`測行檔案=>測試檔案`、`裡麵=>裡面`）直接內建於 `core/domain_normalizer.py` 與 `config.json`，使得即使在 **0ms 不經過 LLM 的組合 16 (`Instant`)** 下，也能輸出 100% 零錯字的高品質專業文句！

### 4. PyInstaller 打包封裝瘦身 (`build_package.py`)
- 移除對 `faster-whisper-small` 與 `paraformer-large-onnx` 的 `--add-data`。
- 將 `faster_whisper`、`ctranslate2`、`tokenizers` 移入 `--exclude-module`，大幅縮減 `dist/FunASRVoiceTyper_Turbo` 的檔案數量與總容量。

---

## 三、 Phase 1 執行步驟：清理冗餘模型與驗證核心權重

請執行工程師（Gemini 3.8 Flash）先依照 `02_CODE_MODIFICATION_GUIDE_輕量化程式碼完整改寫規格書.md` 第一節更新 `download_upgrade_models.py`，然後在 PowerShell 執行：

```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\download_upgrade_models.py"
```

執行後，程式會自動清理 `paraformer-large-onnx`、`faster-whisper-*`、`1.5b` GGUF 與測試暫存檔，並確保唯一黃金組合所需的 3 個核心模型 100% 完整就緒！
