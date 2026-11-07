"""
SPEECH-PIPELINE-HYBRID-FAST: 模組介面契約資料結構定義
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class HybridSegment:
    start_time: float
    end_time: float
    raw_text: str
    corrected_text: str

@dataclass
class HybridTranscriptionResult:
    final_text: str
    raw_text: str
    segments: List[HybridSegment] = field(default_factory=list)
    asr_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    is_fallback: bool = False
