# 03. 驗收測試與輕量打包規範 (v3.3 Verification & Lean Deployment Guide)

在完成 `02_CODE_MODIFICATION_GUIDE_輕量化程式碼完整改寫規格書.md` 的所有模型清理與程式碼改寫後，請嚴格依序執行以下驗收測試、重新封裝與資安稽核。

---

## Step 1：建立並執行 v3.3 黃金輕量版自動化驗收腳本 `test_v33_lean_golden.py`

請在專案根目錄建立 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\test_v33_lean_golden.py`，完整內容如下：

```python
# -*- coding: utf-8 -*-
import os
import sys
import time
import glob
import tempfile
import soundfile as sf
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.asr_engine import Stage1ASREngine
from core.domain_normalizer import normalize_domain_terms
from core.llm_client import LLMCorrectionClient
from core.pipeline import HybridSpeechPipeline

PASS_COUNT = 0
FAIL_COUNT = 0


def assert_test(condition: bool, name: str, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  [PASS] {name} {f'({detail})' if detail else ''}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {name} {f'-> {detail}' if detail else ''}")


def main():
    print("=" * 76)
    print("  FunASRVoiceTyper_Turbo v3.3 (黃金輕量版 組合 16/17/18) 自動化驗收測試")
    print("=" * 76)

    # ---------------------------------------------------------
    # Test 1: 驗證模型硬碟瘦身成果（保留 3 大核心模型，移除冗餘肥大模型）
    # ---------------------------------------------------------
    print("\n[Test 1] 驗證模型瘦身成果與 3 大核心輕量模型完整性...")
    sv_onnx = os.path.join(BASE_DIR, "models", "sensevoice-small-onnx", "model_quant.onnx")
    punc_onnx = os.path.join(BASE_DIR, "models", "punc_ct-transformer_zh-cn-common-vocab272727-onnx", "model_quant.onnx")
    llm_05b = os.path.join(BASE_DIR, "models", "llm", "qwen2.5-0.5b-instruct-q4_k_m.gguf")

    para_dir = os.path.join(BASE_DIR, "models", "paraformer-large-onnx")
    whis_small_dir = os.path.join(BASE_DIR, "models", "faster-whisper-small")
    whis_turbo_dir = os.path.join(BASE_DIR, "models", "faster-whisper-turbo")
    llm_15b_files = glob.glob(os.path.join(BASE_DIR, "models", "**", "*1.5b*.gguf"), recursive=True)

    assert_test(os.path.isfile(sv_onnx) and os.path.getsize(sv_onnx) > 50_000_000,
                "保留黃金 ASR 模型: SenseVoice-Small (model_quant.onnx)",
                f"{os.path.getsize(sv_onnx)/1024/1024:.1f} MB" if os.path.isfile(sv_onnx) else "Missing")
    assert_test(os.path.isfile(punc_onnx) and os.path.getsize(punc_onnx) > 50_000_000,
                "保留黃金標點大模型: CT-Transformer (model_quant.onnx)",
                f"{os.path.getsize(punc_onnx)/1024/1024:.1f} MB" if os.path.isfile(punc_onnx) else "Missing")
    assert_test(os.path.isfile(llm_05b) and os.path.getsize(llm_05b) > 100_000_000,
                "保留黃金語意模型: Qwen2.5-0.5B-Instruct (GGUF)",
                f"{os.path.getsize(llm_05b)/1024/1024:.1f} MB" if os.path.isfile(llm_05b) else "Missing")

    assert_test(not os.path.exists(para_dir), "已徹底移除 Paraformer-large 冗餘目錄")
    assert_test(not os.path.exists(whis_small_dir) and not os.path.exists(whis_turbo_dir),
                "已徹底移除 Faster-Whisper 冗餘目錄")
    assert_test(len(llm_15b_files) == 0, "已徹底移除 Qwen2.5-1.5B 肥大權重檔")

    # ---------------------------------------------------------
    # Test 2: 驗證 main.py 選單精簡（移除模型切換子選單，僅保留打字模式 16/17/18）
    # ---------------------------------------------------------
    print("\n[Test 2] 驗證系統托盤 UI 選單精簡規範...")
    main_py_path = os.path.join(BASE_DIR, "main.py")
    with open(main_py_path, "r", encoding="utf-8") as f:
        main_code = f.read()

    assert_test("語音模型切換 (ASR Model)" not in main_code and "語意重構模型切換" not in main_code,
                "已從系統托盤選單移除『語音模型切換』與『語意重構模型切換』子選單")
    assert_test("打字與段落重編模式 (Typing Mode)" in main_code
                and 'make_mode_setter("instant")' in main_code
                and 'make_mode_setter("typeless")' in main_code
                and 'make_mode_setter("structured")' in main_code,
                "完整保留組合 16 (instant)、組合 17 (typeless)、組合 18 (structured) 打字模式切換")

    # ---------------------------------------------------------
    # Test 3: 驗證組合 16 (SenseVoice + CT-Transformer + Instant 0ms LLM)
    # ---------------------------------------------------------
    print("\n[Test 3] 驗證【組合 16：Instant 極速打字模式 (0ms LLM)】...")
    pipeline = HybridSpeechPipeline(
        asr_model_id="SenseVoice-Small",
        llm_backend="embedded",
        llm_gguf_path="models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    )
    assert_test(pipeline.asr_engine.punc is not None, "CT-Transformer 標點神經網路已掛載就緒")
    assert_test("0.5b" in pipeline.llm_client.model_name.lower(),
                "內嵌語意引擎固定為 Qwen2.5-0.5B", pipeline.llm_client.model_name)

    # 測試 CT-Transformer 標點自動重建
    unpunc = "針對這四個資訊安全工具的測試個別建立一個資料夾裡面要包含預計要測試下載的程試碼或者測型檔案"
    punctuated = pipeline.asr_engine._apply_ct_punc(unpunc)
    cleaned_instant = normalize_domain_terms(punctuated, [])
    assert_test(("，" in cleaned_instant or "。" in cleaned_instant)
                and "程式碼" in cleaned_instant and "測試檔案" in cleaned_instant,
                "組合 16 (0ms LLM) 自動標點與專有名詞秒級校正",
                f"輸出='{cleaned_instant}'")

    # ---------------------------------------------------------
    # Test 4: 驗證組合 17 (SenseVoice + Qwen2.5-0.5B + Typeless 流暢修訂)
    # ---------------------------------------------------------
    print("\n[Test 4] 驗證【組合 17：Typeless 流暢修訂與同音精校模式】...")
    draft_17 = "針對這四個資訊安全工具的測試，個別建立一個資料夾裡麵要包含預計要測試下載的程試碼或者測型檔案。"
    t0 = time.perf_counter()
    res_17 = pipeline.process_Transcript(draft_17, override_mode="typeless")
    ms_17 = (time.perf_counter() - t0) * 1000.0
    out_17 = res_17["final_text"]
    assert_test(not res_17["is_fallback"] and "程式碼" in out_17 and "測試檔案" in out_17 and "裡面" in out_17,
                "組合 17 (Typeless + 0.5B) 精準修訂且無降級",
                f"耗時={ms_17:.0f}ms | 輸出='{out_17}'")

    # ---------------------------------------------------------
    # Test 5: 驗證組合 18 (SenseVoice + Qwen2.5-0.5B + Structured 結構化闡述)
    # ---------------------------------------------------------
    print("\n[Test 5] 驗證【組合 18：Structured 結構化闡述模式】...")
    draft_18 = (
        "那個我們今天主要要討論一下關於桃園大竹國小的韓風熱舞社活動，"
        "第一點我們需要先確認一下場地的租借時間跟音響設備，"
        "第二點就是關於參加人員的名單統計還有保險的部分要趕快處理好。"
    )
    t0 = time.perf_counter()
    res_18 = pipeline.process_Transcript(draft_18, override_mode="structured")
    ms_18 = (time.perf_counter() - t0) * 1000.0
    out_18 = res_18["final_text"]
    assert_test(not res_18["is_fallback"] and len(out_18) >= 20 and ms_18 < 5000,
                "組合 18 (Structured + 0.5B) 極速結構化重編 (< 5000ms)",
                f"耗時={ms_18:.0f}ms | 輸出='{out_18}'")

    print("\n" + "=" * 76)
    print(f"  v3.3 驗收測試總結: PASS={PASS_COUNT}, FAIL={FAIL_COUNT}")
    print("=" * 76)
    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

執行驗收腳本：
```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\test_v33_lean_golden.py"
```
確認所有測試項目皆為 `[PASS]` 且 `FAIL=0`。

---

## Step 2：執行 `build_package.py` 重新打包輕量版執行檔並驗證 `.bat` 規範

執行打包腳本：
```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\build_package.py"
```

打包完成後，請驗證：
1. `dist\FunASRVoiceTyper_Turbo\FunASRVoiceTyper_Turbo.exe` 存在。
2. `dist\FunASRVoiceTyper_Turbo\_internal\models` 下**只有** `sensevoice-small-onnx`、`punc_ct-transformer_zh-cn-common-vocab272727-onnx` 與 `llm\qwen2.5-0.5b-instruct-q4_k_m.gguf`，**絕對沒有** `paraformer`、`faster-whisper` 或 `1.5b` 模型。
3. 所有 `.bat` 批次檔符合 Windows Scripting 規範（100% 純 ASCII 位元組，且採用 `\r\n` CRLF 換行）。

---

## Step 3：執行企業資安稽核腳本

依序執行專案根目錄下的資安審查腳本，確保更新後的模型 SHA-256 清單與靜態安全分析 100% 通過：

```powershell
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\audit_step3_manifest_and_sha.py"
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\audit_step5_sast.py"
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\audit_step7_least_privilege.py"
& "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe" "C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\audit_step1_network.py"
```

當上述步驟全數完成並通過後，即可向使用者回報 v3.3 極致輕量化黃金版部署完成！
