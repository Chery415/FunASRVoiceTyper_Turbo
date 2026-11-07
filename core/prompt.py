"""
SPEECH-PIPELINE-HYBRID-FAST: 提示詞工程標準 (Prompt Specification v3.3 黃金輕量極速版)
核心優化：
1. 採用超精簡 UNIFIED_SYSTEM_PROMPT (~38 tokens) + 固定 User Prompt 共同前綴，
   使 System Prompt 與 User 引導詞在跨模式切換 (typeless <-> structured) 時 100% 鎖定於 KV Prefix Cache！
2. 嚴格要求使用標準繁體中文全形標點（，、。！？），禁止無故插入「- 」連字號或回答問題。
"""

import re
from typing import List, Optional, Tuple

UNIFIED_SYSTEM_PROMPT = (
    "你是繁體中文語音校對專家。請將草稿修正同音錯字、刪贅詞並補上正確全形標點（，、。！？）。"
    "只輸出修訂後文字，嚴禁解釋或加「- 」號。"
)

# 向下相容別名（全部指向同一個鎖定快取的 UNIFIED_SYSTEM_PROMPT）
INSTANT_SYSTEM_PROMPT = UNIFIED_SYSTEM_PROMPT
TYPELESS_SYSTEM_PROMPT = UNIFIED_SYSTEM_PROMPT
STRUCTURED_SYSTEM_PROMPT = UNIFIED_SYSTEM_PROMPT

USER_PREFIX = "草稿："


def _format_terms(domain_terms: Optional[List]) -> str:
    if not domain_terms:
        return "無"
    out = []
    for t in domain_terms:
        if isinstance(t, dict):
            out.extend(str(v) for v in t.values())
        elif isinstance(t, str):
            s = t.strip()
            if not s or s.startswith(("#", "//")):
                continue
            parts = re.split(r'=>|->', s, maxsplit=1)
            out.append(parts[-1].strip())
    seen, uniq = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            uniq.append(x)
    return "、".join(uniq) if uniq else "無"


def build_correction_prompt(
    raw_text: str,
    domain_terms: Optional[List] = None,
    mode: str = "typeless"
) -> Tuple[str, str]:
    """
    建構極速 KV-Cache 友善的 System Prompt 與 User Prompt。
    透過固定 USER_PREFIX，讓跨模式切換時連 User Prompt 的指令前綴也 100% 命中 KV Prefix Cache！
    """
    user_prompt = f"{USER_PREFIX}\n{raw_text.strip()}"
    return UNIFIED_SYSTEM_PROMPT, user_prompt
