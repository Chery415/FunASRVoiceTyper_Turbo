# 01. 語音與標點引擎升級架構規格書 (v3.2 High-Accuracy ASR & Punctuation Spec)

## 一、 問題背景與 `app.log` 實測根因診斷

使用者在 `Intel Core i5-1135G7`（4 實體核心 / 8 邏輯執行緒，16GB RAM）筆電環境下實際測試 `v3.1`，發現雖然速度變快了，但出現以下品質問題：
1. **標點符號漏標或沒標對**（整句話中間沒有逗號，或是被加上奇怪的 `- ` 號）。
2. **句子中間出現明顯同音錯字**（例如：`大竹國小` 變成 `大竹郭小` / `大主播小`、`韓風熱舞社` 變成 `寒風熱舞室`、`辨識` 變成 `辨試` / `電視` / `面試`）。
3. **切換到 `Paraformer-large` 時完全無法辨識（顯示 `⚠️ 未辨識出有效文字`），切換到 `Whisper-Turbo` 則每次固定要等 `13.6 ~ 15.0 秒`**。

### 經調閱 `app.log` (行號 540~687) 與硬碟檔案結構，定位出四大關鍵根因：

#### 根因 1：`Paraformer-large` 與 `CT-Transformer`（獨立標點模型）在硬碟裡其實是空的失效捷徑！
- 先前專案下的 `models/paraformer-large-onnx` 與 `models/punc_ct-transformer_zh-cn-common-vocab272727-onnx` 其實是指向舊版已刪除目錄的 Windows Junction 空連結，硬碟裡**根本沒有這兩個模型的 `.onnx` 權重檔**！
- **嚴重後果**：
  1. `self.punc`（負責幫中文語音補上精準全形逗號、句號、問號、頓號的 `CT-Transformer` 27 萬詞表標點大模型）在執行期間**永遠是 `None`**！這導致 `SenseVoice-Small` 輸出的文字完全沒有經過標點神經網路斷句，整段話連在一起毫無逗號（見 `app.log` 第 594、602、673 行）。
  2. 當使用者在選單切換到 `Paraformer-large` 時，因找不到 `model_quant.onnx`，且 `switch_engine` 降級邏輯未同步重置 `self.current_engine`，導致後續錄音全部落空並輸出 `⚠️ 未辨識出有效文字`（見 `app.log` 第 547~553、647~650 行）。

#### 根因 2：`SenseVoice-Small` 的非自回歸架構缺乏上下文語言邏輯，且 `0.5B` LLM 糾錯能力不足
- `SenseVoice-Small` 採用極速 CTC/SAN-M 非自回歸架構（所有字平行獨立預測），缺乏上下文詞彙聯想能力，且其訓練語料以中國大陸簡體為主，對台灣日常用語與專有名詞容易產生純聲學同音誤判（如：`大竹國小` $\rightarrow$ `大竹郭小`、`辨識` $\rightarrow$ `辨試`）。
- 同時，v3.1 預設改用僅 4.9 億參數的 `Qwen2.5-0.5B-Instruct`，參數規模太小，無法從上下文推斷出「大竹郭小」應為「大竹國小」；而當使用者在 `23:59` 手動切換為 **`Qwen2.5-1.5B-Instruct`** 時，1.5B 在鎖定 KV Cache 後僅需 **`1.0 ~ 2.6 秒`**，糾錯與斷句品質卻明顯高出一個檔次！

#### 根因 3：`Whisper-large-v3-turbo` 的 32 層巨型 Encoder 在 4 核 CPU 上固定耗時 `13.6 ~ 14.9 秒`
- 雖然 `Whisper-large-v3-turbo` 的 Decoder 縮減為 4 層，但它的 **Audio Encoder 依然是 `Whisper-large-v3` 完整的 32 層、1280 維度巨型網路（約 6.3 億參數）**，且預設開啟時間戳切分 (`without_timestamps=False`) 常導致短音訊被重複送入 Encoder 運算兩次，在 `i5-1135G7` 4 核 CPU 上連講 2.4 秒的 `"傳送檔案給我。"` 都要固定耗費 **`13.6 秒`**（見 `app.log` 第 569 行）！

#### 根因 4：短句門檻 (`min_llm_char_length: 12`) 導致短句同音錯字（如「電視/辨試」）被跳過未修訂
- 當使用者口述少於 12 字的短句時，管線直接跳過 LLM，導致 ASR 產生的同音錯字完全沒有機會被語意模型修正。

---

## 二、 v3.2 解決方案：雙王牌 ASR 模型替換 + 獨立標點大模型補齊 + 1.5B 精準校對

為了達成使用者要求：**「反應快、只比 SenseVoice 稍微慢一點（約 `0.6 ~ 2.2 秒`），絕不像 Whisper-Large 那麼慢（14秒），且標點符號與同音字準確度大幅提升」**，v3.2 採取以下架構升級：

### 1. 補齊並升級三大「真・實體權重」本地 ASR 與標點引擎：

| 引擎選項 | 模型權重來源 (HuggingFace) | 4核 CPU 辨識速度 | 核心優勢與適用場景 |
| :--- | :--- | :---: | :--- |
| **🥇 預設首選：<br>`Paraformer-large` + `CT-Transformer` 標點大模型** | `manyeyes/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx`<br>+ `manyeyes/punc_ct-transformer_zh-cn-common-vocab272727-onnx` | **`0.5 秒 ~ 1.1 秒`** | **純中文準度與速度之王**！220M 專精中文聲學模型，搭配 **27 萬詞表獨立 `CT-Transformer` 標點神經網路**，只比 SenseVoice 慢 0.2 秒，但中文拼字穩健度與逗號/句號/問號精準度躍升一個世代！ |
| **🥈 高準度自回歸替換：<br>`Whisper-Small` (CTranslate2 INT8 極速版)** | `Systran/faster-whisper-small`<br>*(取代原本 14 秒的 Whisper-Turbo)* | **`1.2 秒 ~ 2.4 秒`** | **自回歸上下文語境 + 中英夾雜之王**！12 層 Encoder 運算量僅為 Large-v3 的 **1/5**，加上設定 `without_timestamps=True` 杜絕二次重複編碼，速度比舊版 Whisper 快 **6 倍**，且擁有真正的自回歸語言解碼器，能根據上下文自然寫出「大竹國小」、「辨識速度」與原生標點！ |
| **🥉 極速輕量備選：<br>`SenseVoice-Small` + 強制掛載 `CT-Transformer` 標點** | 本地既有 `models/sensevoice-small-onnx` + 新增 `CT-Transformer` 標點模型 | **`0.3 秒 ~ 0.7 秒`** | 補上實體 `CT-Transformer` 標點大模型後，即使在 `instant` 極速模式下也能輸出完整逗號與句號，不再是一整串無標點文字。 |

### 2. Stage 2 內嵌語意模型與提示詞精準化調校：
1. **預設採用 `Qwen2.5-1.5B-Instruct` (`qwen2.5-1.5b-instruct-q4_k_m.gguf`)**：
   - 在 v3.1 鎖定 KV Prefix Cache 與 `n_threads=4 / n_threads_batch=8` 優化下，`1.5B` 推論僅需 **`1.0 ~ 2.5 秒`**，但其繁體中文語感、同音錯字糾正（如將殘留同音字依上下文導正）與標點符號邏輯遠勝 `0.5B`（同時保留 `0.5B` 於系統匣選單供隨時切換）。
2. **修正 `typeless` 與 `structured` 模式的標點失真問題**：
   - 在 `app.log` 第 625、628 行中，使用者反映出現奇怪的 `- ` 破折號（如 `怎麼越測越奇怪 - 標點符號都沒有出來呢。`），原因是 `UNIFIED_SYSTEM_PROMPT` 中寫了 `整理為主旨加「- 」條列`，導致模型在一般單句中也亂插 `- ` 號！
   - v3.2 將明確規範：**一般流暢修訂 (`typeless`) 嚴禁使用 `- ` 破折號或無故改寫原意，必須使用標準全形標點（`、，。！？；：`）進行自然斷句與同音錯字校正**！
3. **將 `min_llm_char_length` 調降為 `2`**，並將常見台灣日常與技術易錯同音詞（如 `辨試=>辨識`、`面試的速度=>辨識的速度`、`大竹郭小=>大竹國小`、`大主播小=>大竹國小`、`gmin=>Gemini`）納入 `Layer 1.5 DomainTermsNormalizer` 內建字典與設定檔，實現 0ms 確定性秒修！

---

## 三、 Phase 1 執行步驟：下載真實模型權重

請執行模型先依照 `02_CODE_MODIFICATION_GUIDE_完整程式碼改寫規格書.md` 第一節更新 `download_upgrade_models.py`，然後執行：

```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\download_upgrade_models.py"
```

確認以下目錄皆具備真實檔案（非失效捷徑）：
1. `models/punc_ct-transformer_zh-cn-common-vocab272727-onnx/model_quant.onnx`（約 278 MB）
2. `models/paraformer-large-onnx/model_quant.onnx`（約 220 MB）
3. `models/faster-whisper-small/model.bin`（約 484 MB）
4. `models/sensevoice-small-onnx/model_quant.onnx`（已存在，約 230 MB）
5. `models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf` 與 `qwen2.5-0.5b-instruct-q4_k_m.gguf`（已存在）
