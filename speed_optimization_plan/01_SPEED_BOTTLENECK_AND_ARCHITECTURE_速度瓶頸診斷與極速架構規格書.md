# 01. 速度瓶頸診斷與 v3.1 極速架構規格書 (Speed Bottleneck Analysis & Ultra-Fast Architecture Spec)

## 一、 專案背景與實測問題現象

使用者在 `Intel Core i5-1135G7`（4 實體核心 / 8 邏輯執行緒，16GB RAM）筆電環境下實際測試 `FunASRVoiceTyper_Turbo v3.0`，嘗試交替使用：
- **三種打字與段落重編模式**：`instant`（極速打字）、`typeless`（流暢修訂與段落重編）、`structured`（結構化闡述與指令）
- **三種本地語音模型**：`Whisper-Turbo`、`SenseVoice-Small`、`Paraformer-large`

實測發現**辨識與處理速度非常慢（數十秒甚至超過 100 秒）**。經調閱真實執行日誌 (`app.log`) 並針對 `llama-cpp-python` 與 `faster-whisper` 進行硬體級剖析測試（Profiling Benchmark），已精準定位出 **5 大核心效能瓶頸**。

---

## 二、 五大效能瓶頸根因剖析（Root-Cause Diagnosis）

### 瓶頸 1：`Whisper-Turbo` 在 4 核心 CPU 上觸發「熱詞重複鬼打牆迴圈 (Hallucination Loop)」（耗時 `20.9 秒 ~ 52.3 秒`）
- **`app.log` 實測證據**：
  - `22:37:14`: `[ASR:52372.4ms, LLM:50647.1ms, 總計:103694.5ms]: 針對這四個資料夾雜証, 資安, 資訊安全工具, 資訊, 資料夾, 資料夾, 資料夾...（連續重複 11 次）`
  - `22:38:12`: `[ASR:20993.3ms, LLM:14900.2ms, 總計:36081.8ms]: 我們再來測試案例，資訊安全與資訊安全。資訊安全與資訊安全...（連續重複 12 次）`
- **技術根因**：
  1. `core/asr_engine.py` 同時將 34 個 `domain_terms` 塞進 `initial_prompt` 與 `hotwords` 參數，且未設定 `repetition_penalty` 與 `no_repeat_ngram_size`，在語音尾端或停頓處觸發 Whisper Decoder 經典的「熱詞自回歸無限重複迴圈」，直到塞滿最大 Token 數才停下，導致單次 ASR 在 4 核 CPU 上卡死 21~52 秒，還把長達數百字的重複垃圾字串餵給後端 LLM，連帶害 LLM 又再算 15~50 秒！
  2. 相較之下，同時間 `app.log` 紀錄顯示 **`SenseVoice-Small` (ONNX)** 與 **`Paraformer-large` (ONNX)** 辨識短中句僅需 **`110ms ~ 899ms`（0.1~0.9 秒）**，辨識 30 秒長段落也僅需 **`2,623ms`（2.6 秒）**！

### 瓶頸 2：肥大的 System Prompt (`1,069 tokens`) + 切換模式導致 `llama.cpp` KV Prefix Cache 100% 失效重算（耗時 `7.1 秒 ~ 50.6 秒`）
- **剖析實驗與 `app.log` 證據**：
  - `core/prompt.py` 中的 `TYPELESS_SYSTEM_PROMPT` 包含大量冗長規則與兩大段長篇範例，加上 `user_prompt` 內嵌 34 個專有名詞，單次輸入 Prompt 高達 **`1,069 tokens`**！
  - 在 `i5-1135G7` 純 CPU 上，首次評估（Prompt Evaluation）1,069 tokens 需耗時 **`29.5 秒 ~ 45.5 秒`**！
  - 更嚴重的是：
    1. `warmup()` 預熱時只傳了 `[{"role": "user", "content": "好"}]`，完全沒有預熱 `system_prompt`，導致使用者第一次錄音必吃 30~45 秒冷啟動懲罰。
    2. `INSTANT_SYSTEM_PROMPT`、`TYPELESS_SYSTEM_PROMPT`、`STRUCTURED_SYSTEM_PROMPT` 三者的 System Prompt 字串完全不同！只要使用者在系統匣切換模式（如 `instant` 切 `typeless` 或 `structured`），`llama.cpp` 內部的 Prefix KV Cache 就會 **100% 失效（Cache Miss）**，導致就算只講兩個字 `"檔案檔案。"`，LLM 也要重新計算數百至上千個 Prompt Tokens，耗時 **`7.1 秒 ~ 14.2 秒`**（見 `app.log` `22:42:32` `[ASR:110.3ms, LLM:7104.8ms]`、`22:43:10` `[ASR:126.7ms, LLM:14244.4ms]`）。
  - **關鍵對照證據**：在 `app.log` `22:48:15` ~ `22:48:30`，當使用者連續三次不切換模式時，`llama.cpp` 命中 Prefix Cache，LLM 耗時瞬間從 `14,244ms` 暴降至 **`554.7ms ~ 892.3ms`（僅 0.5~0.8 秒）**！

### 瓶頸 3：`llama.cpp` 在 4 核 8 緒 CPU 上的 Hyperthreading 超執行緒搶占問題（生成速度慢 **3.1 倍**）
- **硬體實測數據**：
  - `Intel Core i5-1135G7` 擁有 **4 顆實體核心 (Physical Cores)** 與 **8 條邏輯執行緒 (Logical Threads)**。
  - 經基準測試驗證，在自回歸逐字生成階段（Token Generation，受限於記憶體頻寬與快取同步）：
    - 設定 `n_threads=8`：生成 45 tokens 耗時 **`5.16 秒`**（超執行緒嚴重互相搶奪 AVX2 浮點單元與 L1/L2 Cache）。
    - 設定 `n_threads=4`（實體核心數）且 `n_threads_batch=8`（Prompt 批次並行數）：生成相同內容僅需 **`1.67 秒`**，**速度直接提升 3.1 倍**！

### 瓶頸 4：`instant`（極速打字模式）與簡短口令不必要地呼叫了 Stage 2 LLM
- 在 `instant`（極速打字模式）下，使用者的訴求是「講完立刻出字，只修同音錯字與補標點」。
- 事實上，Stage 1 (`SenseVoice-Small` / `Paraformer-large` + `CT-Transformer` 神經網路標點) 加上 Layer 1.5 (`DomainTermsNormalizer` 模糊拼音同音校正 + 顯式詞庫替換 + 口語疊字消除 + `ITNNormalizer` + `OpenCC`)，在 **`0.5 毫秒`** 內就已經完成了同音字修正、專有名詞對齊與標點補齊！
- v3.0 卻在 `instant` 模式下依然呼叫 GGUF LLM，白白浪費數秒鐘等待。同理，在 `typeless` / `structured` 模式下，少於 12 個字的簡短句子（例如 `"請幫我執行測試。"`、`"確認一下這個程式。"`）根本不需要「段落重新編排」，直接走 Layer 1.5 快速通道即可在 **0.2 秒** 內瞬間上屏。

### 瓶頸 5：純 CPU 環境下 `1.5B` 模型與 `0.5B` 模型的生成吞吐量差異
- 在無 GPU 加速的純 CPU 商務筆電上，`Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`（約 398MB）的每秒 Token 生成速度（tok/s）是 `1.5B`（約 1.1GB）的 **2.6 ~ 3.0 倍**，且記憶體佔用減少 65%。
- 透過提供 `0.5B 極速輕量模型` 作為預設內嵌引擎（並保留 `1.5B 標準模型` 供系統匣隨時切換），長段落重編可在 **0.5 秒 ~ 1.5 秒** 內瞬間完成！

---

## 三、 v3.1 極速流暢架構設計與效能目標 (Target Architecture)

```
[使用者按下 Right Ctrl 停止錄音]
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 1: 本機高速語音轉錄 (ASR Engine)                                   │
│ - 預設推薦：SenseVoice-Small (ONNX INT8) + CT-Transformer 標點 (0.15~0.6s)│
│ - 備選 1：Paraformer-large (ONNX INT8) + CT-Transformer 標點 (0.3~0.9s)  │
│ - 備選 2：Whisper-Turbo (CT2 INT8, 啟用防鬼打牆參數與精簡熱詞)           │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Layer 1.5: 零延遲本機確定性語意清洗 (< 1ms)                              │
│ - 口語填充贅字/結巴疊字/半截重複片語消除 (_remove_stutters)               │
│ - 34+ 組專有名詞顯式對照與模糊拼音同音字強制校正 (DomainTermsNormalizer)  │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 智慧分流路由器 (Smart Mode & Length Router)                              │
│ 判斷條件：                                                               │
│  1. 若 typing_mode == "instant" (極速打字模式) ──► 【直接走極速通道】     │
│  2. 若有效字數 < 12 字 (簡短單句，無須段落重組) ──► 【直接走極速通道】     │
│  3. 若 typing_mode 為 "typeless"/"structured" 且字數 >= 12 ──► 【進 LLM】│
└───────────────────┬─────────────────────────────────────┬───────────────┘
                    │ 【極速通道 Fast-Path】               │ 【長句重編通道】
                    │ (LLM 耗時 = 0.0 ms!)                ▼
                    │                     ┌───────────────────────────────┐
                    │                     │ Stage 2: 極速內嵌 GGUF 引擎    │
                    │                     │ - 單一 85-token 固定 System   │
                    │                     │   Prompt (切換模式永不失效!)   │
                    │                     │ - 開機預熱鎖定 KV Prefix Cache │
                    │                     │ - n_threads=4 (實體核),       │
                    │                     │   n_threads_batch=8 (批次核)   │
                    │                     │ - Qwen2.5-0.5B / 1.5B 可切換  │
                    │                     └───────────────┬───────────────┘
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Post-Processing: ITN 數字正規化 + OpenCC 台灣繁中 + 專有名詞最終鎖定     │
│ ──► TextInjector 剪貼簿秒速貼上 (總體感延遲：極速模式 ~0.2s / 重編 ~1.2s)│
└─────────────────────────────────────────────────────────────────────────┘
```

### 改善前後延遲對比表（於 `i5-1135G7` 實測基準）

| 使用情境 | v3.0 改善前耗時 | v3.1 改善後目標耗時 | 改善幅度 |
| :--- | :--- | :--- | :--- |
| **🟢 極速打字模式 (`instant`)** | `7.2 秒 ~ 14.3 秒` | **`0.15 秒 ~ 0.6 秒`** (`LLM: 0.0ms`) | **快 20 倍以上** |
| **🟣/🔵 短句口述 (`< 12` 字)** | `7.1 秒 ~ 14.2 秒` | **`0.15 秒 ~ 0.4 秒`** (`LLM: 0.0ms`) | **快 25 倍以上** |
| **🟣/🔵 切換模式後首次中長句重編** | `14.2 秒 ~ 45.5 秒` (KV Cache 失效) | **`0.6 秒 ~ 1.8 秒`** (KV Cache 100% 命中) | **快 15 ~ 25 倍** |
| **🟣/🔵 長篇段落重編 (`100+` 字)** | `25.0 秒 ~ 50.6 秒` | **`1.2 秒 ~ 2.8 秒`** | **快 15 倍以上** |
| **Whisper-Turbo 含專有名詞口述** | `20.9 秒 ~ 52.3 秒` (重複迴圈卡死) | **`1.5 秒 ~ 4.5 秒`** (零重複迴圈) | **徹底根除卡死** |

---

## 四、 Phase 1 執行步驟：下載極速版 `Qwen2.5-0.5B-Instruct-GGUF` 模型

請執行模型先依照 `02_CODE_MODIFICATION_GUIDE_極速化程式碼完整改寫規格書.md` 第一節更新 `download_upgrade_models.py`，然後在專案虛擬環境中執行：

```powershell
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe download_upgrade_models.py
```

確認 `models/llm/` 目錄下同時具備：
1. `models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf`（約 398 MB，v3.1 預設極速模型）
2. `models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf`（約 1.1 GB，備選深度模型，已存在無須重抓）
