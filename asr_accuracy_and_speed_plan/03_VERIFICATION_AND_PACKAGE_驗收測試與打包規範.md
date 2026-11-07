# 03_VERIFICATION_AND_PACKAGE_驗收測試與打包規範 (v3.2 準度與標點強化驗收規範)

在完成 `02_CODE_MODIFICATION_GUIDE_完整程式碼改寫規格書.md` 的所有模型下載與程式碼改寫後，請嚴格執行本文件的自動化驗收測試、重新打包與企業資安稽核。

---

## Step 1：建立並執行 v3.2 準度與標點自動化驗收腳本 `test_v32_asr_and_punc.py`

請在專案根目錄建立 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\test_v32_asr_and_punc.py`，完整內容如下：

```python
import os
import sys
import time
import json
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager
from core.asr_engine import Stage1ASREngine
from core.domain_normalizer import DomainNormalizer
from core.llm_client import Stage2LLMRefiner
from core.pipeline import TwoStageVoicePipeline

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
    print("=" * 72)
    print("FunASRVoiceTyper_Turbo v3.2 語音模型與標點準度自動化驗收測試")
    print("=" * 72)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = ConfigManager("config.json")

    # ---------------------------------------------------------
    # Test 1: 檢查實體模型檔案是否完整且非損壞 Junction
    # ---------------------------------------------------------
    print("\n[Test 1] 檢查新增與修復之本地模型檔案完整性...")
    punc_onnx = os.path.join(base_dir, "models", "punc_ct-transformer_zh-cn-common-vocab272727-onnx", "model_quant.onnx")
    para_onnx = os.path.join(base_dir, "models", "paraformer-large-onnx", "model_quant.onnx")
    whis_small = os.path.join(base_dir, "models", "faster-whisper-small", "model.bin")
    llm_15b = os.path.join(base_dir, "models", "llm", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

    assert_test(os.path.isfile(punc_onnx) and os.path.getsize(punc_onnx) > 50_000_000,
                "CT-Transformer 標點大模型 (model_quant.onnx)",
                f"Exists={os.path.isfile(punc_onnx)}, Size={os.path.getsize(punc_onnx)/1024/1024:.1f}MB" if os.path.isfile(punc_onnx) else "Missing")
    assert_test(os.path.isfile(para_onnx) and os.path.getsize(para_onnx) > 100_000_000,
                "Paraformer-large 旗艦中文模型 (model_quant.onnx)",
                f"Exists={os.path.isfile(para_onnx)}, Size={os.path.getsize(para_onnx)/1024/1024:.1f}MB" if os.path.isfile(para_onnx) else "Missing")
    assert_test(os.path.isfile(whis_small) and os.path.getsize(whis_small) > 200_000_000,
                "Faster-Whisper-Small 均衡模型 (model.bin)",
                f"Exists={os.path.isfile(whis_small)}, Size={os.path.getsize(whis_small)/1024/1024:.1f}MB" if os.path.isfile(whis_small) else "Missing")
    assert_test(os.path.isfile(llm_15b),
                "Qwen2.5-1.5B-Instruct GGUF 模型",
                f"Exists={os.path.isfile(llm_15b)}")

    # ---------------------------------------------------------
    # Test 2: 驗證 CT-Transformer 獨立標點模型載入與斷句能力
    # ---------------------------------------------------------
    print("\n[Test 2] 驗證 Stage 1 ASR 引擎與 CT-Transformer 獨立標點斷句...")
    asr = Stage1ASREngine(cfg.config)
    assert_test(asr.punc is not None, "Stage1ASREngine.punc (CT_Transformer) 必須成功載入非 None")

    raw_unpunctuated = "好我們再來測一次現在我把模型切換到那個最快速的模型我們現在來看一下它整體的辨識速度是不是有變得比較快"
    t0 = time.perf_counter()
    punctuated = asr._apply_ct_punc(raw_unpunctuated)
    punc_ms = (time.perf_counter() - t0) * 1000
    has_comma_or_period = ("，" in punctuated) or ("。" in punctuated) or ("？" in punctuated)
    assert_test(has_comma_or_period and len(punctuated) > len(raw_unpunctuated),
                "CT-Transformer 無標點長句自動補齊標點",
                f"耗時={punc_ms:.1f}ms | 輸出='{punctuated}'")

    # ---------------------------------------------------------
    # Test 3: 驗證三大主力 ASR 模型動態切換與推論穩定性
    # ---------------------------------------------------------
    print("\n[Test 3] 驗證三大主力 ASR 模型 (Paraformer-large / Whisper-Small / SenseVoice-Small) 載入與推論...")
    dummy_audio = np.zeros(16000 * 2, dtype=np.float32)

    for model_key in ["paraformer-large", "whisper-small", "sensevoice-small"]:
        t_sw = time.perf_counter()
        ok = asr.switch_model(model_key)
        sw_ms = (time.perf_counter() - t_sw) * 1000
        res = asr.transcribe(dummy_audio, language="zh", hotwords=["大竹國小", "鴻海"])
        assert_test(ok and asr.model_type == model_key and "text" in res,
                    f"切換並推論模型 [{model_key}]",
                    f"切換耗時={sw_ms:.0f}ms, backend={res.get('backend')}")

    # 切回預設 paraformer-large
    asr.switch_model("paraformer-large")

    # ---------------------------------------------------------
    # Test 4: 驗證 Layer 1.5 同音字正規化與 Stage 2 1.5B 精修無「- 」符號污染
    # ---------------------------------------------------------
    print("\n[Test 4] 驗證同音錯字校正與消除無故『- 』條列符號污染...")
    pipeline = TwoStageVoicePipeline(cfg, asr_engine=asr)

    typo_input = "好，我們現在來到大竹郭小跟寒風熱舞室測試語音辨試的速度。"
    t0 = time.perf_counter()
    res_typeless = pipeline.process_Transcript(typo_input, override_mode="typeless")
    el_ms = (time.perf_counter() - t0) * 1000
    final_typeless = res_typeless["final_text"]

    assert_test("大竹國小" in final_typeless and "韓風熱舞社" in final_typeless and "辨識" in final_typeless,
                "同音錯字精準校正 (大竹國小 / 韓風熱舞社 / 辨識)",
                f"耗時={el_ms:.0f}ms | 輸出='{final_typeless}'")
    assert_test(not final_typeless.startswith("- ") and "\n- " not in final_typeless,
                "單句潤飾模式禁止出現『- 』符號污染",
                f"輸出='{final_typeless}'")

    # ---------------------------------------------------------
    # Test 5: 驗證長段落重編 (Paragraph Reflow) 速度與品質
    # ---------------------------------------------------------
    print("\n[Test 5] 驗證長段落重編 (Paragraph Reflow) 標點與結構重組...")
    rambling = (
        "那個我們今天主要要討論一下關於桃園大竹國小的韓風熱舞社活動，"
        "呃其實就是說第一點我們需要先確認一下場地的租借時間跟音響設備，"
        "然後呢第二點就是關於參加人員的名單統計還有保險的部分要趕快處理好，"
        "最後一點就是預算需要在禮拜五之前交給財務部門審核。"
    )
    t0 = time.perf_counter()
    res_para = pipeline.process_Transcript(rambling, override_mode="paragraph")
    para_ms = (time.perf_counter() - t0) * 1000
    final_para = res_para["final_text"]
    assert_test(para_ms < 5500 and len(final_para) >= 25,
                "Paragraph 長段落重編 (< 5500ms 且結構完整)",
                f"耗時={para_ms:.0f}ms | 輸出=\n{final_para}")

    print("\n" + "=" * 72)
    print(f"測試總結: PASS={PASS_COUNT}, FAIL={FAIL_COUNT}")
    print("=" * 72)
    if FAIL_COUNT > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

執行測試：
```powershell
.\env\python.exe test_v32_asr_and_punc.py
```
確認所有測試項目皆顯示 `[PASS]` 且 `FAIL=0`。

---

## Step 2：同步更新舊版測試腳本以保持向後相容

為確保 `test_upgrade_pipeline.py` 與 `test_speed_optimization.py` 也能在 v3.2 預設配置下通過：
1. 檢查 `test_speed_optimization.py`：若其中檢查 `default_model == "sensevoice-small"` 或 `0.5b`，請將其放寬為允許 `paraformer-large` 與 `1.5b`（或以 `test_v32_asr_and_punc.py` 作為主驗收測試）。

---

## Step 3：執行 `build_package.py` 重新封裝 v3.2 單一免安裝執行檔

執行打包腳本：
```powershell
.\env\python.exe build_package.py
```

打包完成後，請驗證：
1. `dist\FunASRVoiceTyper_Turbo\FunASRVoiceTyper_Turbo.exe` 存在。
2. `dist\FunASRVoiceTyper_Turbo\models\paraformer-large-onnx\model_quant.onnx` 存在。
3. `dist\FunASRVoiceTyper_Turbo\models\punc_ct-transformer_zh-cn-common-vocab272727-onnx\model_quant.onnx` 存在。
4. `dist\FunASRVoiceTyper_Turbo\models\faster-whisper-small\model.bin` 存在。
5. `dist\FunASRVoiceTyper_Turbo\啟動語音輸入_極速版.bat` 經檢查包含 `\r\n` (CRLF) 且無任何大於 127 的非 ASCII 位元組。

---

## Step 4：執行企業資安稽核腳本

依序執行專案根目錄下的資安審查腳本，確保 100% 符合無網路連線、無未授權修改與最小權限原則：

```powershell
.\env\python.exe audit_step3_manifest_and_sha.py
.\env\python.exe audit_step5_sast.py
.\env\python.exe audit_step7_least_privilege.py
.\env\python.exe audit_step1_network.py
```

當上述步驟全數 `[PASS]` 後，即可向使用者回報 v3.2 升級完成！
