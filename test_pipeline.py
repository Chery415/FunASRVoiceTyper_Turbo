"""
SPEECH-PIPELINE-HYBRID-FAST: 系統規格檢驗與單元測試 (含 ITN 逆文本正規化與標點斷句)
"""

import os
import sys
import time
import tempfile
import numpy as np

# 加入根目錄至 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import HybridSegment, HybridTranscriptionResult
from core.prompt import build_correction_prompt, SYSTEM_PROMPT
from core.pipeline import HybridSpeechPipeline
from core.itn_normalizer import normalize_itn

def create_sample_wav() -> str:
    """建立一個 2 秒的測試音訊檔案"""
    import soundfile as sf
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    audio = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sr)
    tmp.close()
    return tmp.name

def test_itn_normalizer():
    print("[測試 1] 逆文本正規化 (ITN Normalizer) 檢驗...")
    test_cases = [
        ("八十percent", "80%"),
        ("百分之八十", "80%"),
        ("成長了三點五percent", "成長了3.5%"),
        ("室溫大約二十五度c", "室溫大約25°C"),
        ("二零二六年會有三加五等於八的情況", "2026年會有3 + 5 = 8的情況"),
        ("一百二十個產品", "120個產品"),
    ]
    for inp, expected in test_cases:
        actual = normalize_itn(inp)
        print(f"  [ITN] '{inp}' -> '{actual}'")
        assert expected in actual, f"ITN 轉換失敗: 預期包含 '{expected}'，但得到 '{actual}'"
    print("  => 通過！口語數字、百分比與數學符號轉換完全正確。")

def test_prompt_specification():
    print("\n[測試 2] 提示詞工程標準 2.0 (Prompt Specification) 檢驗...")
    raw_text = "今天討論台積電與cowos先進封裝，市佔率達到八十percent"
    domain_terms = ["台積電", "CoWoS", "先進封裝"]
    
    sys_p, usr_p = build_correction_prompt(raw_text, domain_terms)
    
    assert "繁體中文（台灣）" in sys_p, "System prompt 缺少繁體中文台灣規則！"
    assert "只輸出修正後的最終文字" in sys_p, "System prompt 缺少無額外輸出規則！"
    assert "80%" in sys_p or "數字與符號書寫規範" in sys_p, "System prompt 缺少 ITN 規範！"
    assert "斷句與排版規範" in sys_p, "System prompt 缺少斷句排版規範！"
    assert "專有名詞參考: 台積電, CoWoS, 先進封裝" in usr_p, "User prompt 未正確注入 domain_terms！"
    print("  => 通過！Prompt 規則完整涵蓋專有名詞、ITN 與斷句規範。")

def test_fallback_strategy_with_itn(wav_path: str):
    print("\n[測試 3] LLM 離線降級備援 + 本地 ITN 雙重保障檢驗...")
    # 指向一個不存在的 LLM 埠號，模擬逾時或離線
    offline_pipeline = HybridSpeechPipeline(
        asr_model_id="iic/SenseVoiceSmall",
        llm_api_base="http://127.0.0.1:59999/v1",
        llm_model_name="qwen2.5:3b-instruct-q4_K_M",
        device="cpu"
    )

    # 模擬 ASR 輸出帶有口語百分比與數字符號的初稿
    offline_pipeline.asr_engine.transcribe = lambda audio: (
        "今天討論半導體先進製程cowos技術，市佔率達到八十percent",
        [{"start": 0.0, "end": 2.0, "text": "今天討論半導體先進製程cowos技術，市佔率達到八十percent"}]
    )

    result = offline_pipeline.process(
        audio_path=wav_path,
        domain_terms=["半導體", "製程", "CoWoS"],
        enable_correction=True,
        llm_timeout_seconds=0.3
    )

    print(f"  原始語音: '今天討論半導體先進製程cowos技術，市佔率達到八十percent'")
    print(f"  降級標記 (is_fallback): {result.is_fallback}")
    print(f"  最終輸出 (final_text): {result.final_text}")
    print(f"  ASR 延遲: {result.asr_latency_ms:.2f} ms")
    print(f"  LLM 延遲: {result.llm_latency_ms:.2f} ms")

    assert result.is_fallback is True, "LLM 離線應標記 is_fallback=True！"
    assert "80%" in result.final_text, "本地 ITN 應將『八十percent』成功轉為『80%』！"
    assert "，" in result.final_text, "輸出應保留完整標點斷句！"
    print("  => 通過！即使 LLM 離線，輸出依然具備標準斷句標點與 80% 符號轉換！")

def test_simulated_llm_correction(wav_path: str):
    print("\n[測試 4] 模擬 LLM 在線校正檢驗...")
    pipeline = HybridSpeechPipeline(device="cpu")
    pipeline.asr_engine.transcribe = lambda audio: (
        "台積電最新euv半導體製程技術說明，市佔率達到百分之八十",
        [{"start": 0.0, "end": 2.0, "text": "台積電最新euv半導體製程技術說明，市佔率達到百分之八十"}]
    )
    
    class MockSuccessLLMClient:
        def correct_text(self, system_prompt, user_prompt, timeout_seconds=0.8):
            return "台積電最新 EUV 半導體製程技術說明，市佔率達到 80%。", 85.5, True

    pipeline.llm_client = MockSuccessLLMClient()
    
    result = pipeline.process(
        audio_path=wav_path,
        domain_terms=["台積電", "EUV", "半導體製程"],
        enable_correction=True
    )

    print(f"  初稿文字: '{result.raw_text}'")
    print(f"  校正輸出: '{result.final_text}'")
    print(f"  是否降級: {result.is_fallback}")

    assert result.is_fallback is False
    assert "EUV" in result.final_text
    assert "80%" in result.final_text
    assert "。" in result.final_text
    print("  => 通過！")

def test_offline_domain_terms_correction(wav_path: str):
    print("\n[測試 5] 本機離線專有名詞、自訂別名與同音字校正檢驗...")
    offline_pipeline = HybridSpeechPipeline(
        asr_model_id="SenseVoice-Small",
        llm_api_base="http://127.0.0.1:59999/v1",
        device="cpu"
    )

    # 模擬語音辨識產生台灣常見同音字：「城市」(程式)、「治安」(資安)、「cowos」(CoWoS)
    offline_pipeline.asr_engine.transcribe = lambda audio: (
        "請留下這一個城市版本就好，其他的都刪除。參考檔案的治安測試審查做法，幫我進行治安檢核測試，治安長會過目。另外請討論cowos架構。",
        [{"start": 0.0, "end": 2.0, "text": "mock"}]
    )

    terms = [
        "台積電", "CoWoS", "EUV", "先進製程", "晶圓代工", "半導體", "AI", "API", "Meeting",
        "程式", "資安長", "資安"
    ]

    result = offline_pipeline.process(
        audio_path=wav_path,
        domain_terms=terms,
        enable_correction=True,
        llm_timeout_seconds=0.3
    )

    print(f"  ASR 初稿: '請留下這一個城市版本就好...進行治安檢核測試，治安長會過目...討論cowos架構'")
    print(f"  最終校正: '{result.final_text}'")

    assert "程式" in result.final_text, "同音字『城市』應校正為專有名詞『程式』！"
    assert "資安" in result.final_text, "同音字『治安』應校正為專有名詞『資安』！"
    assert "資安長" in result.final_text, "同音字『治安長』應校正為專有名詞『資安長』！"
    assert "CoWoS" in result.final_text, "英文縮寫『cowos』應規範化為『CoWoS』！"
    print("  => 通過！本機離線狀態下專有名詞、大小寫與同音字 100% 精準自動校正！")

def main():
    print("=================================================================")
    print("   SPEECH-PIPELINE-HYBRID-FAST: 規格升級與全項檢驗")
    print("=================================================================")
    wav_path = create_sample_wav()
    try:
        test_itn_normalizer()
        test_prompt_specification()
        test_fallback_strategy_with_itn(wav_path)
        test_simulated_llm_correction(wav_path)
        test_offline_domain_terms_correction(wav_path)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

    print("\n=================================================================")
    print("   所有升級測試全數通過！斷句標點與數字符號 (ITN) 運作完美。")
    print("=================================================================")

if __name__ == "__main__":
    main()
