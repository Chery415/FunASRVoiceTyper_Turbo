# 🛡️ FunASRVoiceTyper_Turbo v3.0 — 測試驗收、綠色打包與資安檢驗規範 (Packaging & Security Audit Guide)

> **執行說明**：在完成 `02_CODE_MODIFICATION_GUIDE_程式碼完整改寫規格書.md` 的所有程式碼修改後，請執行模型（Gemini 3.8 Flash）依序執行本文件的 Step 3.1 ～ Step 3.3，確保所有新功能、段落重編品質、PyInstaller 綠色封裝與企業資安檢核 100% 通過。

---

## Step 3.1：建立並執行端到端自動化驗收腳本 `test_upgrade_pipeline.py`

**目標路徑**：`C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\test_upgrade_pipeline.py`

### 驗收目標：
1. 驗證 `Stage1ASREngine` 成功載入本地 `Whisper-Turbo` (CTranslate2 INT8) 並支援與 `SenseVoice-Small` 熱切換。
2. 驗證 `Layer 1.5 (DomainTermsNormalizer)` 能正確清除助詞疊字（`的的`）、半截重複（`把連結把`）與英文聽寫誤植（`integravity` $\rightarrow$ `Antigravity`、`cloucoo` $\rightarrow$ `Claude Code`、`reno 4` $\rightarrow$ `Linux`）。
3. 驗證 `Stage 2 (LLMCorrectionClient Embedded GGUF)` 在**完全不啟動 Ollama、不開任何網路 Port** 的狀態下，能於進程記憶體內對長段口述草稿進行：
   - **`typeless` 模式**：吸收停頓與重複語句，重新編排並流暢闡述整段內容。
   - **`structured` 模式**：將多步驟口述需求整理為條理分明的結構化清單。

### 完整腳本內容：
```python
# coding: utf-8
"""
test_upgrade_pipeline.py
FunASRVoiceTyper_Turbo v3.0 全內嵌雙引擎端到端自動化驗收腳本
"""

import json
import time
import numpy as np
from core.domain_normalizer import normalize_domain_terms, extract_hotwords_list
from core.prompt import build_correction_prompt
from core.pipeline import HybridSpeechPipeline


def run_verification():
    with open("config.json", "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    domain_terms = cfg.get("domain_terms", [])

    print("=" * 70)
    print(" [測試 1] 驗證熱詞萃取與 Layer 1.5 口語疊字/半截重複/專有名詞清洗")
    print("=" * 70)
    hotwords = extract_hotwords_list(domain_terms)
    print(f"✓ 萃取聲學熱詞數量: {len(hotwords)} -> 前 10 項: {hotwords[:10]}")

    raw_sample_1 = "呃那個實驗類的的指令碼，把連結把公佈出來的連線網址提供給我，然後然後確認一下germin跟integravity還有cloucoo的設定。"
    cleaned_1 = normalize_domain_terms(raw_sample_1, domain_terms)
    print(f"原始口語草稿: {raw_sample_1}")
    print(f"Layer1.5清洗: {cleaned_1}")
    assert "的的" not in cleaned_1, "助詞疊字『的的』未被消除"
    assert "把連結把" not in cleaned_1, "半截重複『把連結把』未被消除"
    assert "Antigravity" in cleaned_1 and "Claude Code" in cleaned_1, "專有名詞映射未生效"
    print("✓ [測試 1] 通過！\n")

    print("=" * 70)
    print(" [測試 2] 初始化 HybridSpeechPipeline v3.0 (Whisper-Turbo + 內嵌 GGUF)")
    print("=" * 70)
    pipeline = HybridSpeechPipeline(
        asr_model_id=cfg.get("asr_model_id", "Whisper-Turbo"),
        llm_backend=cfg.get("llm_backend", "embedded"),
        llm_gguf_path=cfg.get("llm_gguf_path", "models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        device="cpu"
    )

    assert pipeline.asr_engine.get_current_engine_name() == "Whisper-Turbo", "Whisper-Turbo 未成功設為主引擎"
    assert pipeline.is_llm_online(), "內嵌 GGUF LLM 未成功上線"
    assert pipeline.warmup_llm(), "內嵌 GGUF LLM 預熱失敗"

    # 測試靜音/短音訊推論不崩潰
    dummy_audio = np.zeros(16000 * 1, dtype=np.float32)
    raw_txt, _ = pipeline.asr_engine.transcribe(dummy_audio, domain_terms=domain_terms)
    print(f"✓ Whisper-Turbo 靜音防呆測試通過 (輸出: '{raw_txt}')\n")

    print("=" * 70)
    print(" [測試 3] 驗證 Stage 2 內嵌 GGUF LLM — 整段語意理解、去贅字與段落重新編排")
    print("=" * 70)

    # 取自使用者真實歷史 log 中語句重複、不順暢之長段落案例
    long_rambling_draft = (
        "針對這四個資訊安全工具的測試，個別建立一個資料夾裡面，要個別包含預計要測試下載的程式碼或者是測型檔案。"
        "每個別針對這四個工具，把他們實際下載下來的檔案都放在這裡。"
        "測試的過程要包含測試的歷程的記錄，每一個測試步驟都要有相應的截圖來證明說實際有針對測試的測試碼或者是模型進行測試。"
        "最後個別針對測試的結果，最生一份測試的結果報告。"
    )
    precleaned_long = normalize_domain_terms(long_rambling_draft, domain_terms)

    # 測試 Typeless 流暢修訂與段落重編模式
    sys_p, usr_p = build_correction_prompt(precleaned_long, domain_terms=domain_terms, mode="typeless")
    t0 = time.perf_counter()
    revised_typeless, elapsed_ms, ok = pipeline.llm_client.correct_text(sys_p, usr_p, timeout_seconds=20.0)
    assert ok and revised_typeless, "Typeless 段落重編失敗"
    print(f"【原始長段草稿】:\n{long_rambling_draft}\n")
    print(f"【Typeless 流暢修訂與段落重編結果 (耗時 {elapsed_ms:.1f}ms)】:\n{revised_typeless}\n")

    # 測試 Structured 結構化闡述與指令模式
    sys_s, usr_s = build_correction_prompt(precleaned_long, domain_terms=domain_terms, mode="structured")
    revised_structured, elapsed_s_ms, ok_s = pipeline.llm_client.correct_text(sys_s, usr_s, timeout_seconds=20.0)
    assert ok_s and revised_structured, "Structured 結構化重組失敗"
    print(f"【Structured 結構化闡述結果 (耗時 {elapsed_s_ms:.1f}ms)】:\n{revised_structured}\n")

    print("🎉 所有 v3.0 測試項目 100% 通過！")


if __name__ == "__main__":
    run_verification()
```

### 執行驗收指令：
```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" test_upgrade_pipeline.py
```

---

## Step 3.2：更新綠色免安裝打包腳本 `build_package.py`

**目標路徑**：`C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\build_package.py`

### 修改重點：
將 `models/faster-whisper-turbo` 與 `models/llm`（內含 `.gguf` 語意重構模型），以及 `faster_whisper`、`ctranslate2`、`llama_cpp`、`tokenizers`、`av` 一併封裝進 `dist/FunASRVoiceTyper_Turbo` 單一綠色目錄中，確保使用者將該資料夾複製到公司電腦後，**免安裝 Ollama、免安裝 Python、免管理員權限即可直接執行**。

### 完整替換內容：
```python
"""
FunASRVoiceTyper_Turbo v3.0 企業綠色免安裝版打包建置腳本
- 採用 --onedir 目錄型封裝，免安裝外部軟體、免管理員權限
- 內嵌 faster-whisper (CTranslate2 INT8) + FunASR ONNX + 內嵌 GGUF 語意重構模型 (llama-cpp-python)
- 排除未使用的肥大依賴（如 torch、matplotlib 等），維持純淨安全架構
"""

import os
import PyInstaller.__main__

base_dir = os.path.dirname(os.path.abspath(__file__))
whisper_dir = os.path.abspath(os.path.join(base_dir, "models", "faster-whisper-turbo"))
llm_dir = os.path.abspath(os.path.join(base_dir, "models", "llm"))
sensevoice_dir = os.path.abspath(os.path.join(base_dir, "models", "sensevoice-small-onnx"))
paraformer_dir = os.path.abspath(os.path.join(base_dir, "models", "paraformer-large-onnx"))
punc_dir = os.path.abspath(os.path.join(base_dir, "models", "punc_ct-transformer_zh-cn-common-vocab272727-onnx"))
config_file = os.path.join(base_dir, "config.json")

print("=================================================================")
print("  開始打包 FunASRVoiceTyper_Turbo v3.0 (全內嵌雙引擎企業綠色版)")
print("=================================================================")

args = [
    os.path.join(base_dir, "main.py"),
    "--noconsole",
    "--onedir",
    f"--add-data={config_file};.",
]

for src_dir, target_rel in [
    (whisper_dir, "models/faster-whisper-turbo"),
    (llm_dir, "models/llm"),
    (sensevoice_dir, "models/sensevoice-small-onnx"),
    (paraformer_dir, "models/paraformer-large-onnx"),
    (punc_dir, "models/punc_ct-transformer_zh-cn-common-vocab272727-onnx"),
]:
    if os.path.exists(src_dir):
        print(f"納入模型目錄: {src_dir} -> {target_rel}")
        args.append(f"--add-data={src_dir};{target_rel}")

args.extend([
    "--collect-all=faster_whisper",
    "--collect-all=ctranslate2",
    "--collect-all=tokenizers",
    "--collect-all=llama_cpp",
    "--collect-all=opencc",
    "--collect-all=pystray",
    "--collect-all=sounddevice",
    "--collect-all=funasr_onnx",
    "--collect-all=onnxruntime",
    "--collect-all=jieba",
    "--collect-all=pypinyin",
    "--collect-all=scipy",
    # 瘦身排除項目（嚴禁打包 PyTorch）
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    "--exclude-module=torchaudio",
    "--exclude-module=matplotlib",
    "--exclude-module=pytest",
    "--exclude-module=unittest",
    "--exclude-module=IPython",
    "--name=FunASRVoiceTyper_Turbo",
    "--clean",
    "-y"
])

PyInstaller.__main__.run(args)
print("\n=================================================================")
print("  打包完成！產出位於 dist/FunASRVoiceTyper_Turbo 資料夾")
print("=================================================================")
```

---

## Step 3.3：執行資安審查檢核確認 (Security Audit Verification)

完成程式碼修改與測試後，請執行以下指令驗證專案完全符合企業資安規範：

1. **更新 SBOM 與模型 SHA-256 校驗清單**：
   ```powershell
   & "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" audit_step3_manifest_and_sha.py
   ```
2. **執行網路隔離與零對外連線檢驗**：
   ```powershell
   & "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" audit_step1_network.py
   ```
   *(確認輸出包含 `零活動 TCP 連線` 與 `無任何開放之 Listening Port`)*
3. **執行 Bandit SAST 靜態原始碼安全掃描**：
   ```powershell
   & "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" -m bandit -r main.py core -f json -o security_audit\attachments\06_sast_bandit_report.json
   & "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" audit_step5_sast.py
   ```
   *(確認 `SEVERITY.HIGH: 0`)*

---

## ✅ 最終交付檢核表 (Completion Checklist for Gemini 3.8 Flash)

當你（Gemini 3.8 Flash）完成所有步驟向使用者回報時，請逐一勾選確認以下項目：
- [ ] `faster-whisper` 與 `llama-cpp-python` 已成功安裝於 `.venv`，且完全未安裝 `torch`。
- [ ] `models/faster-whisper-turbo` 與 `models/llm/*.gguf` 模型權重已下載完畢。
- [ ] `config.json`、`core/domain_normalizer.py`、`core/asr_engine.py`、`core/prompt.py`、`core/llm_client.py`、`core/pipeline.py`、`core/wave_overlay.py`、`main.py` 皆已依規格書更新。
- [ ] `test_upgrade_pipeline.py` 執行結果為 **ALL TESTS PASSED**，實測證明長段落可自動去贅字、融合重複語句並重新編排為流暢段落。
- [ ] `audit_step1_network.py` 與 `audit_step5_sast.py` 資安檢測全數通過（0 TCP 連線、0 開放 Port、0 高風險漏洞）。
