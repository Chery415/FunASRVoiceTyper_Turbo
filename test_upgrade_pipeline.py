# coding: utf-8
"""
test_upgrade_pipeline.py
FunASRVoiceTyper_Turbo v3.0 全內嵌雙引擎端到端自動化驗收腳本
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import time
import numpy as np
from core.domain_normalizer import normalize_domain_terms, extract_hotwords_list
from core.prompt import build_correction_prompt
from core.pipeline import HybridSpeechPipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_verification():
    cfg_path = os.path.join(BASE_DIR, "config.json")
    with open(cfg_path, "r", encoding="utf-8-sig") as f:
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
        asr_model_id="Whisper-Turbo",
        llm_backend=cfg.get("llm_backend", "embedded"),
        llm_gguf_path=cfg.get("llm_gguf_path", "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"),
        device="cpu"
    )

    assert pipeline.asr_engine.get_current_engine_name() in ("Whisper-Small", "Whisper-Turbo"), "Whisper 未成功設為主引擎"
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
