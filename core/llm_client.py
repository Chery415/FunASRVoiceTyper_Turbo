"""
SPEECH-PIPELINE-HYBRID-FAST: 本地 LLM 語意重構與同音糾錯引擎 (v3.3 黃金輕量版)
專注於實測速度與性價比第一名之 Qwen2.5-0.5B-Instruct (Q4_K_M)：
1. 100% 透過 llama-cpp-python 於進程記憶體內直接推論 (In-Process Inference)，零網路模組。
2. 保留 1 顆實體核心給 OS 與 ONNX Runtime，避免 4 核心 CPU 發生 Spinlock 搶占。
3. 開機預熱直接鎖定 UNIFIED_SYSTEM_PROMPT 的 KV Prefix Cache，切換模式零延遲。
"""

import os
import sys
import re
import glob
import logging
import time
import threading
from typing import Optional, Tuple, List

from core.prompt import UNIFIED_SYSTEM_PROMPT, USER_PREFIX

logger = logging.getLogger("HybridLLMClient")


def _get_search_roots() -> List[str]:
    roots = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            roots.append(sys._MEIPASS)
        exe_dir = os.path.dirname(sys.executable)
        roots.append(exe_dir)
        roots.append(os.path.join(exe_dir, "_internal"))
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roots.extend([
        root_dir,
        os.path.join(root_dir, "dist", "FunASRVoiceTyper_Turbo"),
        os.path.join(root_dir, "dist", "FunASRVoiceTyper_Turbo", "_internal"),
    ])
    return roots


def resolve_gguf_model_path(configured_rel_path: str = "") -> Optional[str]:
    """在所有可能的封裝路徑中尋找本地 Qwen2.5-0.5B .gguf 模型檔案"""
    roots = _get_search_roots()
    if configured_rel_path:
        if os.path.isabs(configured_rel_path) and os.path.exists(configured_rel_path):
            return configured_rel_path
        for r in roots:
            candidate = os.path.abspath(os.path.join(r, configured_rel_path))
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return candidate

    for r in roots:
        for pattern in [
            os.path.join(r, "models", "llm", "*0.5b*.gguf"),
            os.path.join(r, "models", "llm", "*.gguf"),
            os.path.join(r, "models", "*.gguf")
        ]:
            matches = sorted(glob.glob(pattern))
            if matches:
                return os.path.abspath(matches[0])
    return None


class LLMCorrectionClient:
    def __init__(
        self,
        api_base: str = "http://localhost:11434/v1",
        model_name: str = "qwen2.5:0.5b-instruct-q4_K_M",
        api_key: str = "",
        backend: str = "embedded",
        gguf_path: str = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    ):
        self.backend = "embedded"
        self.gguf_path = gguf_path
        self.resolved_gguf_path: Optional[str] = None
        self._llama = None
        self._lock = threading.Lock()
        self.api_base = api_base
        self.model_name = model_name
        self.api_key = api_key

        self._init_embedded_llama()

    def _init_embedded_llama(self) -> bool:
        if self._llama is not None:
            return True
        gguf_file = resolve_gguf_model_path(self.gguf_path)
        if not gguf_file:
            logger.warning(f"找不到本地 GGUF 模型檔 (設定路徑: {self.gguf_path})，請執行 download_upgrade_models.py")
            return False
        try:
            from llama_cpp import Llama
            logical_cpus = os.cpu_count() or 4
            phys_cores = max(2, logical_cpus // 2)
            # 保留 1 顆實體核心給 OS 與 ONNX Runtime，避免 i5-1135G7 4核 CPU 發生 Spinlock 搶占
            opt_threads = 3 if phys_cores >= 4 else phys_cores
            gen_threads = opt_threads
            batch_threads = opt_threads
            logger.info(
                f"正在載入內嵌 GGUF 語意重構模型 (gen_threads={gen_threads}, batch_threads={batch_threads}): {gguf_file}"
            )
            self._llama = Llama(
                model_path=gguf_file,
                n_ctx=512,
                n_threads=gen_threads,
                n_threads_batch=batch_threads,
                n_batch=512,
                n_gpu_layers=0,
                verbose=False
            )
            self.resolved_gguf_path = gguf_file
            self.model_name = os.path.basename(gguf_file)
            logger.info(f"內嵌 GGUF 模型載入成功: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"載入內嵌 GGUF 模型失敗: {e}")
            self._llama = None
            return False

    def switch_gguf_model(self, new_gguf_rel_path: str = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf") -> str:
        """向下相容介面：保持使用 Qwen2.5-0.5B 模型"""
        if self._llama is None:
            self._init_embedded_llama()
            self.warmup()
        return self.model_name

    def warmup(self, timeout_seconds: float = 60.0) -> bool:
        """預熱模型並將 UNIFIED_SYSTEM_PROMPT 預先鎖入 llama.cpp 的 KV Prefix Cache"""
        if self._llama is None and not self._init_embedded_llama():
            return False
        try:
            t0 = time.perf_counter()
            with self._lock:
                self._llama.create_chat_completion(
                    messages=[
                        {"role": "system", "content": UNIFIED_SYSTEM_PROMPT},
                        {"role": "user", "content": f"{USER_PREFIX}\n測試預熱。"}
                    ],
                    max_tokens=4,
                    temperature=0.0
                )
            ms = (time.perf_counter() - t0) * 1000.0
            logger.info(f"內嵌 GGUF 模型與 KV Prefix Cache 預熱完成 ({ms:.1f}ms): {self.model_name}")
            return True
        except Exception as e:
            logger.warning(f"內嵌 GGUF 模型預熱例外: {e}")
            return False

    def is_online(self, cache_ttl: float = 4.0) -> bool:
        return self._llama is not None

    def correct_text(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 8.0
    ) -> Tuple[Optional[str], float, bool]:
        if not self.is_online() or self._llama is None:
            return None, 0.0, False

        t_start = time.perf_counter()
        try:
            max_tok = max(48, min(256, int(len(user_prompt) * 1.4) + 16))
            with self._lock:
                resp = self._llama.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    repeat_penalty=1.0,
                    max_tokens=max_tok,
                    stop=["<|im_end|>", "<|endoftext|>"]
                )
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            content = resp["choices"][0]["message"]["content"].strip()
            cleaned = self._clean_llm_output(content)
            if cleaned and len(cleaned) <= max(len(user_prompt) * 2.4, 50):
                return cleaned, elapsed_ms, True
            return None, elapsed_ms, False
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            logger.error(f"內嵌 GGUF 推論發生例外: {e} (耗時: {elapsed_ms:.1f}ms)")
            return None, elapsed_ms, False

    def _clean_llm_output(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        if text.startswith("```") and text.endswith("```"):
            lines = text.split("\n")
            if len(lines) >= 3:
                text = "\n".join(lines[1:-1]).strip()

        text = re.sub(
            r'^(?:以下是(?:修訂|修改|整理|重組)後的(?:內容|文字|結果|段落)[：:\s]*|(?:輸出|修正後|修訂後|結果)\s*[:：]\s*)',
            '',
            text
        ).strip()

        if (text.startswith('"') and text.endswith('"')) or (text.startswith('「') and text.endswith('」')):
            text = text[1:-1].strip()

        if "\n" not in text:
            text = re.sub(r'^(?:-\s+|\d+\.\s+)', '', text).strip()
            text = re.sub(r'\s+-\s+', '，', text)

        return text


Stage2LLMRefiner = LLMCorrectionClient
