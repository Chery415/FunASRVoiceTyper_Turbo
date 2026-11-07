"""
SPEECH-PIPELINE-HYBRID-FAST v3.3 (Lean Golden Edition):
專注於實測最佳之 16 / 17 / 18 黃金組合：
- Stage 1: SenseVoice-Small + CT-Transformer 27萬詞表標點大模型 (極速高準度)
- Layer 1.5: 口語疊字/半截重複清洗與 50+ 專有名詞/同音詞強制對齊 (< 0.5ms)
- Stage 2: 內嵌 Qwen2.5-0.5B-Instruct (KV Cache 常駐鎖定，支援 Instant 0ms / Typeless / Structured 三種模式)
"""

import time
import logging
from typing import List, Optional, Union, Any

try:
    import opencc
    _cc = opencc.OpenCC('s2twp')
except Exception:
    _cc = None

from core.models import HybridSegment, HybridTranscriptionResult
from core.prompt import build_correction_prompt
from core.llm_client import LLMCorrectionClient
from core.asr_engine import Stage1ASREngine
from core.itn_normalizer import normalize_itn
from core.domain_normalizer import normalize_domain_terms

logger = logging.getLogger("HybridSpeechPipeline")


class HybridSpeechPipeline:
    def __init__(
        self,
        asr_model_id: Union[str, dict, Any] = "SenseVoice-Small",
        llm_api_base: str = "http://localhost:11434/v1",
        llm_model_name: str = "qwen2.5:0.5b-instruct-q4_K_M",
        device: str = "cpu",
        llm_api_key: str = "",
        llm_backend: str = "embedded",
        llm_gguf_path: str = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        asr_engine: Optional[Stage1ASREngine] = None
    ):
        if hasattr(asr_model_id, "config"):
            cfg = getattr(asr_model_id, "config", {})
            asr_model_id = "SenseVoice-Small"
            llm_api_base = cfg.get("llm_api_base", llm_api_base)
            llm_model_name = cfg.get("llm_model_name", llm_model_name)
            llm_api_key = cfg.get("llm_api_key", llm_api_key)
            llm_backend = cfg.get("llm_backend", llm_backend)
            llm_gguf_path = cfg.get("llm_gguf_path", llm_gguf_path)
        elif isinstance(asr_model_id, dict):
            cfg = asr_model_id
            asr_model_id = "SenseVoice-Small"
            llm_api_base = cfg.get("llm_api_base", llm_api_base)
            llm_model_name = cfg.get("llm_model_name", llm_model_name)
            llm_api_key = cfg.get("llm_api_key", llm_api_key)
            llm_backend = cfg.get("llm_backend", llm_backend)
            llm_gguf_path = cfg.get("llm_gguf_path", llm_gguf_path)

        self.device = device
        self.llm_api_base = llm_api_base
        self.llm_model_name = llm_model_name
        self.llm_backend = llm_backend
        self.llm_gguf_path = llm_gguf_path

        if asr_engine is not None:
            self.asr_engine = asr_engine
            self.asr_model_id = asr_engine.get_current_engine_name()
        else:
            logger.info(f"正在初始化 Stage 1 ASR 引擎 (SenseVoice-Small + CT-Transformer, device={device})...")
            self.asr_engine = Stage1ASREngine(default_engine="SenseVoice-Small", device=device)
            self.asr_model_id = self.asr_engine.get_current_engine_name()

        logger.info(f"正在初始化 Stage 2 LLM 引擎 (backend={llm_backend}, gguf={llm_gguf_path})...")
        self.llm_client = LLMCorrectionClient(
            api_base=llm_api_base,
            model_name=llm_model_name,
            api_key=llm_api_key,
            backend=llm_backend,
            gguf_path=llm_gguf_path
        )
        if self.is_llm_online():
            self.warmup_llm()
        logger.info("HybridSpeechPipeline v3.3 (黃金輕量版) 初始化完成。")

    def is_llm_online(self) -> bool:
        return self.llm_client.is_online(cache_ttl=0.0)

    def warmup_llm(self) -> bool:
        return self.llm_client.warmup()

    def switch_model(self, model_name: str = "SenseVoice-Small") -> str:
        self.asr_model_id = self.asr_engine.switch_engine(model_name)
        return self.asr_model_id

    def switch_llm_model(self, gguf_rel_path: str = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf") -> str:
        return self.llm_client.switch_gguf_model(gguf_rel_path)

    def process_Transcript(self, text: str, override_mode: str = "typeless") -> dict:
        """針對已有草稿文字進行 Stage 2 語意與標點精修"""
        mode_low = (override_mode or "typeless").lower()
        if mode_low == "paragraph":
            mode_low = "structured"
        domain_terms = []
        precleaned = normalize_domain_terms(text, domain_terms)
        if mode_low == "instant":
            final_t = normalize_itn(precleaned)
            if _cc and final_t:
                final_t = _cc.convert(final_t)
            return {
                "final_text": final_t,
                "raw_text": text,
                "latency_ms": 0.0,
                "is_fallback": False
            }
        sys_prompt, user_prompt = build_correction_prompt(precleaned, domain_terms=domain_terms, mode=mode_low)
        corrected, elapsed, success = self.llm_client.correct_text(sys_prompt, user_prompt, timeout_seconds=15.0)
        final_t = corrected if (success and corrected) else precleaned
        final_t = normalize_itn(final_t)
        if _cc and final_t:
            final_t = _cc.convert(final_t)
        final_t = normalize_domain_terms(final_t, domain_terms)
        return {
            "final_text": final_t,
            "raw_text": text,
            "latency_ms": elapsed,
            "is_fallback": not success
        }

    def process(
        self,
        audio_path: str,
        domain_terms: Optional[List[str]] = None,
        enable_correction: bool = True,
        llm_timeout_seconds: float = 8.0,
        typing_mode: str = "typeless",
        min_llm_char_length: int = 2
    ) -> HybridTranscriptionResult:
        t_pipeline_start = time.perf_counter()

        # ---------------------------------------------------------
        # 階段一推論 (Stage 1 SenseVoice-Small + CT-Transformer 獨立標點神經網路)
        # ---------------------------------------------------------
        t_asr_start = time.perf_counter()
        raw_text, raw_segments = self.asr_engine.transcribe(audio_path, domain_terms=domain_terms)
        asr_latency_ms = (time.perf_counter() - t_asr_start) * 1000.0

        if _cc and raw_text:
            raw_text = _cc.convert(raw_text)

        if not raw_text.strip():
            total_latency_ms = (time.perf_counter() - t_pipeline_start) * 1000.0
            return HybridTranscriptionResult(
                final_text="", raw_text="", segments=[],
                asr_latency_ms=round(asr_latency_ms, 2),
                llm_latency_ms=0.0, total_latency_ms=round(total_latency_ms, 2),
                is_fallback=False
            )

        # ---------------------------------------------------------
        # 預處理層 (Layer 1.5): 口語疊字消除與專有名詞/同音詞強制對齊 (< 0.5ms)
        # ---------------------------------------------------------
        precleaned_text = normalize_domain_terms(raw_text, domain_terms or [])

        # ---------------------------------------------------------
        # 階段二：語意同音糾錯與段落重構 (組合 16: Instant / 組合 17: Typeless / 組合 18: Structured)
        # ---------------------------------------------------------
        final_text = precleaned_text
        llm_latency_ms = 0.0
        is_fallback = False

        mode_low = (typing_mode or "typeless").lower()
        cleaned_len = len(precleaned_text.strip("，。！？、,.!? "))

        should_call_llm = (
            enable_correction
            and mode_low in ("typeless", "structured")
            and cleaned_len >= max(2, int(min_llm_char_length))
        )

        if should_call_llm:
            sys_prompt, user_prompt = build_correction_prompt(
                precleaned_text,
                domain_terms=domain_terms,
                mode=mode_low
            )
            effective_timeout = max(float(llm_timeout_seconds), 4.0 + len(precleaned_text) * 0.06)

            corrected_text, llm_elapsed_ms, success = self.llm_client.correct_text(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                timeout_seconds=effective_timeout
            )
            llm_latency_ms = llm_elapsed_ms

            if success and corrected_text:
                final_text = corrected_text
                is_fallback = False
            else:
                logger.warning(f"Stage 2 LLM 未能完成修訂 (耗時 {llm_latency_ms:.1f}ms)，採用 Layer 1.5 預清洗結果。")
                final_text = precleaned_text
                is_fallback = True

        # ---------------------------------------------------------
        # 後處理雙重防護：對最終文字進行 ITN 逆文本正規化、繁中轉換與詞庫鎖定
        # ---------------------------------------------------------
        final_text = normalize_itn(final_text)
        if _cc and final_text:
            final_text = _cc.convert(final_text)

        final_text = normalize_domain_terms(final_text, domain_terms or [])

        segments: List[HybridSegment] = []
        for s in raw_segments:
            seg_raw = s.get("text", "")
            if _cc and seg_raw:
                seg_raw = _cc.convert(seg_raw)
            seg_corr = final_text if len(raw_segments) == 1 else seg_raw
            segments.append(HybridSegment(
                start_time=round(s.get("start", 0.0), 3),
                end_time=round(s.get("end", 0.0), 3),
                raw_text=seg_raw,
                corrected_text=seg_corr
            ))

        total_latency_ms = (time.perf_counter() - t_pipeline_start) * 1000.0

        return HybridTranscriptionResult(
            final_text=final_text,
            raw_text=raw_text,
            segments=segments,
            asr_latency_ms=round(asr_latency_ms, 2),
            llm_latency_ms=round(llm_latency_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
            is_fallback=is_fallback
        )


TwoStageVoicePipeline = HybridSpeechPipeline
