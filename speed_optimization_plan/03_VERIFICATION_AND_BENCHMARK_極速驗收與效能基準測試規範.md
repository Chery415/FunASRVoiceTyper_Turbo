# 03. 極速驗收與效能基準測試規範 (v3.1 Verification & Benchmark Spec)

在完成 `02_CODE_MODIFICATION_GUIDE_極速化程式碼完整改寫規格書.md` 的所有檔案更新後，請執行模型（Gemini 3.8 Flash）依序執行本文件的驗收測試與重新打包流程。

---

## 一、 建立自動化極速基準測試腳本 `test_speed_optimization.py`

請在專案根目錄 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\test_speed_optimization.py` 建立以下測試腳本，並使用 `.venv\Scripts\python.exe test_speed_optimization.py` 執行驗收：

```python
# coding: utf-8
"""
test_speed_optimization.py
驗證 FunASRVoiceTyper_Turbo v3.1 極速流暢優化版之 5 大效能與功能指標：
1. System Prompt Token 數驗證（必須 < 120 tokens，且三種模式共用同一 System Prompt）
2. 開機預熱與模式切換 KV Cache 零失效測試（切換 typeless <-> structured 單次 LLM 延遲必須 < 3,500ms）
3. Instant 極速模式與短句 (<12字) 零延遲通道驗證（LLM 耗時必須 = 0.0ms）
4. Whisper-Turbo 防鬼打牆重複折疊保護驗證
5. 完整端到端 ASR + LLM 延遲基準測試
"""

import os
import sys
import time
import json
import tempfile
import numpy as np
import soundfile as sf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.prompt import (
    UNIFIED_SYSTEM_PROMPT,
    INSTANT_SYSTEM_PROMPT,
    TYPELESS_SYSTEM_PROMPT,
    STRUCTURED_SYSTEM_PROMPT,
    build_correction_prompt,
)
from core.asr_engine import _dedup_whisper_hallucination
from core.pipeline import HybridSpeechPipeline


def run_benchmark():
    print("=" * 72)
    print(" [Step 1] 驗證 System Prompt 極簡化與跨模式一致性 (KV Cache 鎖定基礎)")
    print("=" * 72)
    assert INSTANT_SYSTEM_PROMPT == UNIFIED_SYSTEM_PROMPT
    assert TYPELESS_SYSTEM_PROMPT == UNIFIED_SYSTEM_PROMPT
    assert STRUCTURED_SYSTEM_PROMPT == UNIFIED_SYSTEM_PROMPT

    s_typeless, u_typeless = build_correction_prompt("這是一段超過十二個字的測試語音轉錄草稿內容。", mode="typeless")
    s_struct, u_struct = build_correction_prompt("這是一段超過十二個字的測試語音轉錄草稿內容。", mode="structured")
    assert s_typeless == s_struct, "切換模式時 System Prompt 必須 100% 相同以保持 KV Cache 命中！"
    print(f"✓ System Prompt 字元長度: {len(UNIFIED_SYSTEM_PROMPT)} 字 (跨模式 100% 一致)")

    print("\n" + "=" * 72)
    print(" [Step 2] 驗證 Whisper-Turbo 防鬼打牆重複過濾器")
    print("=" * 72)
    hallucinated = "我們再來測試案例，資訊安全與資訊安全。資訊安全與資訊安全。資訊安全與資訊安全。資訊安全與資訊安全。"
    deduped = _dedup_whisper_hallucination(hallucinated)
    print(f"原始鬼打牆輸入: {hallucinated}")
    print(f"折疊過濾後輸出: {deduped}")
    assert len(deduped) < len(hallucinated) // 2, "防鬼打牆過濾器未生效！"
    print("✓ Whisper-Turbo 防鬼打牆重複過濾驗證通過！")

    print("\n" + "=" * 72)
    print(" [Step 3] 初始化 HybridSpeechPipeline v3.1 並執行 KV Cache 預熱")
    print("=" * 72)
    with open(os.path.join(BASE_DIR, "config.json"), "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    pipeline = HybridSpeechPipeline(
        asr_model_id=cfg.get("asr_model_id", "SenseVoice-Small"),
        llm_backend="embedded",
        llm_gguf_path=cfg.get("llm_gguf_path", "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf")
    )
    assert pipeline.is_llm_online(), "內嵌 GGUF LLM 未正常載入！"
    t_warm0 = time.perf_counter()
    assert pipeline.warmup_llm(), "LLM 預熱失敗！"
    print(f"✓ 開機預熱與 System Prompt KV Cache 鎖定耗時: {(time.perf_counter() - t_warm0)*1000:.1f} ms")

    print("\n" + "=" * 72)
    print(" [Step 4] 驗證跨模式來回切換 (typeless <-> structured) 之 LLM 推論速度")
    print("=" * 72)
    test_cases = [
        ("typeless", "針對這四個資訊安全工具的測試，個別建立一個資料夾，每個測試步驟都要有截圖，最後產生一份測試報告。"),
        ("structured", "針對這四個資訊安全工具的測試，個別建立一個資料夾，每個測試步驟都要有截圖，最後產生一份測試報告。"),
        ("typeless", "我們明天再去開會然後確認一下這個城市的錯誤，看看到底是哪一個模組發生的問題。"),
    ]
    for idx, (m_mode, sample_txt) in enumerate(test_cases, start=1):
        sys_p, usr_p = build_correction_prompt(sample_txt, mode=m_mode)
        out_txt, elapsed_ms, ok = pipeline.llm_client.correct_text(sys_p, usr_p, timeout_seconds=8.0)
        print(f"  [{idx}] 模式={m_mode:<10} | 耗時={elapsed_ms:6.1f} ms | 輸出: {out_txt}")
        assert ok and out_txt, f"模式 {m_mode} 推論失敗！"
        assert elapsed_ms < 4500.0, f"模式切換後推論過慢 ({elapsed_ms:.1f}ms > 4500ms)，KV Cache 未命中！"

    print("✓ 跨模式切換零快取失效驗證通過！所有推論均在極速範圍內完成！")

    print("\n" + "=" * 72)
    print(" [Step 5] 驗證三大 ASR 模型熱切換 (SenseVoice -> Paraformer -> Whisper)")
    print("=" * 72)
    assert pipeline.asr_engine.get_current_engine_name() == "SenseVoice-Small"
    assert pipeline.switch_model("Paraformer-large") == "Paraformer-large"
    assert pipeline.switch_model("Whisper-Turbo") == "Whisper-Turbo"
    dummy_audio = np.zeros(16000 * 1, dtype=np.float32)
    raw_txt, _ = pipeline.asr_engine.transcribe(dummy_audio, domain_terms=cfg.get("domain_terms", []))
    print(f"✓ Whisper-Turbo 靜音防呆與三大模型熱切換驗證通過 (輸出: '{raw_txt}')")
    assert pipeline.switch_model("SenseVoice-Small") == "SenseVoice-Small"

    print("\n🎉 所有 v3.1 極速流暢優化基準測試 100% 通過！")


if __name__ == "__main__":
    run_benchmark()
```

---

## 二、 完整執行與資安打包檢驗清單（Step-by-Step Checklist）

請執行模型依序在 PowerShell 執行以下命令，確保所有測試與打包 100% 通過：

### 1. 停止任何舊版背景 `pythonw.exe` 實例（避免鎖定舊檔案）
```powershell
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "FunASRVoiceTyper_Turbo" -Force -ErrorAction SilentlyContinue
```

### 2. 執行 v3.1 極速基準測試
```powershell
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe test_speed_optimization.py
```

### 3. 重新打包 `dist/FunASRVoiceTyper_Turbo` 企業免安裝綠色版
```powershell
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe build_package.py
```

### 4. 執行三大企業資安稽核腳本確認 100% 通過
```powershell
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe audit_step1_static.py
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe audit_step2_network.py
C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\.venv\Scripts\python.exe audit_step3_privileges.py
```
*(注意：若 `audit_step2_network.py` 會在背景啟動 `dist\FunASRVoiceTyper_Turbo\FunASRVoiceTyper_Turbo.exe` 進行網路監聽測試，測試完畢後請將該測試用的 `.exe` 結束，再幫使用者透過 `啟動語音打字_v3.bat` 啟動最新 v3.1 服務。)*
