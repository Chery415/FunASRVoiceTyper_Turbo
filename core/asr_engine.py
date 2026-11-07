"""
Stage1ASREngine v3.3 (Lean Golden Edition):
專注於實測綜合表現第一名之單一黃金語音引擎：
- SenseVoice-Small (ONNX INT8) + CT-Transformer 27萬詞表獨立標點大模型 (ONNX INT8)
- 徹底移除 Faster-Whisper 與 Paraformer 冗餘分支，大幅降低記憶體佔用與啟動時間。
"""

import os
import sys
import re
import json
import logging
from typing import Tuple, List, Dict, Any, Optional, Union
import numpy as np

try:
    import yaml
except Exception:
    yaml = None

try:
    import opencc
    _cc = opencc.OpenCC('s2twp')
except Exception:
    _cc = None

logger = logging.getLogger("Stage1ASREngine")


class TranscriptionResult:
    """
    同時支援 Tuple 解構 `raw_text, segments = engine.transcribe(...)`
    與 Dict 存取 `res["text"]`、`res.get("backend")` 之結果封裝物件。
    """
    def __init__(self, text: str, segments: List[Dict[str, Any]], backend: str = "SenseVoice-Small"):
        self.text = text
        self.segments = segments
        self.backend = backend

    def __iter__(self):
        yield self.text
        yield self.segments

    def __getitem__(self, key):
        if isinstance(key, int):
            return (self.text, self.segments)[key]
        if key == "text":
            return self.text
        if key == "segments":
            return self.segments
        if key == "backend":
            return self.backend
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return key in ("text", "segments", "backend")


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
        os.path.join(root_dir, "..", "FunASRVoiceTyper_Turbo"),
    ])
    return roots


def resolve_model_dir(rel_subpath: str) -> Optional[str]:
    """解析 ONNX 模型目錄（確保模型檔案真實存在）"""
    for r in _get_search_roots():
        abs_c = os.path.abspath(os.path.join(r, rel_subpath))
        if os.path.exists(abs_c) and (
            os.path.exists(os.path.join(abs_c, "model_quant.onnx"))
            or os.path.exists(os.path.join(abs_c, "model.onnx"))
        ):
            return abs_c
    return None


def _dedup_whisper_hallucination(text: str) -> str:
    """向下相容輔助函式：移除連續重複超過 2 次以上的片語或詞組"""
    if not text:
        return ""
    cleaned = re.sub(r'(.{2,15}?)(?:[，、,\s]*\1){2,}', r'\1', text)
    cleaned = re.sub(r'([，。！？、,.!?])\1+', r'\1', cleaned)
    return cleaned.strip()


class Stage1ASREngine:
    def __init__(self, default_engine: Union[str, dict] = "SenseVoice-Small", device: str = "cpu"):
        self.device = device
        self.current_engine = "sensevoice"
        self.sensevoice_model = None
        self.punc = None
        self._init_models()

    @property
    def model_type(self) -> str:
        return "sensevoice-small"

    def _init_models(self):
        """預先載入 CT-Transformer 獨立標點模型與 SenseVoice-Small 主語音引擎"""
        self._init_punc_model()
        self._load_sensevoice()

    def _load_sensevoice(self) -> bool:
        if self.sensevoice_model is not None:
            return True
        sv_path = resolve_model_dir(os.path.join("models", "sensevoice-small-onnx"))
        if sv_path:
            try:
                from funasr_onnx import SenseVoiceSmall
                phys_cores = max(2, min(4, (os.cpu_count() or 4) // 2))
                logger.info(f"載入本機 SenseVoice-Small ONNX 權重 (intra_op={phys_cores}): {sv_path}")
                self.sensevoice_model = SenseVoiceSmall(
                    sv_path,
                    batch_size=1,
                    quantize=True,
                    intra_op_num_threads=phys_cores
                )
                logger.info("SenseVoice-Small ONNX 模型載入成功。")
                self._init_punc_model()
                return True
            except Exception as e:
                logger.error(f"SenseVoice-Small 載入失敗: {e}")
        return False

    def _init_punc_model(self):
        if self.punc is not None:
            return
        punc_path = resolve_model_dir(os.path.join("models", "punc_ct-transformer_zh-cn-common-vocab272727-onnx"))
        if punc_path:
            try:
                punc_yaml = os.path.join(punc_path, "punc.yaml")
                config_yaml = os.path.join(punc_path, "config.yaml")
                if yaml and os.path.exists(punc_yaml):
                    need_fix = True
                    if os.path.exists(config_yaml):
                        try:
                            with open(config_yaml, "r", encoding="utf-8") as f:
                                cdata = yaml.safe_load(f)
                            if cdata and "model_conf" in cdata and "punc_list" in cdata["model_conf"]:
                                need_fix = False
                        except Exception:
                            need_fix = True
                    if need_fix:
                        with open(punc_yaml, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        if "model_conf" not in data:
                            data["model_conf"] = {}
                        data["model_conf"]["punc_list"] = data.get("punc_list", ['<unk>', '_', ',', '。', '?', '、'])
                        with open(config_yaml, "w", encoding="utf-8") as f:
                            yaml.dump(data, f, allow_unicode=True)

                tok_txt = os.path.join(punc_path, "tokens.txt")
                tok_json = os.path.join(punc_path, "tokens.json")
                if os.path.exists(tok_txt) and not os.path.exists(tok_json):
                    with open(tok_txt, "r", encoding="utf-8") as f:
                        tokens = [line.strip("\r\n") for line in f]
                    with open(tok_json, "w", encoding="utf-8") as f:
                        json.dump(tokens, f, ensure_ascii=False)

                from funasr_onnx import CT_Transformer
                logger.info(f"載入本機 CT-Transformer 標點大模型: {punc_path}")
                self.punc = CT_Transformer(punc_path, quantize=True, intra_op_num_threads=2)
                logger.info("CT-Transformer 標點大模型載入成功，已啟用 27萬詞表神經網絡自動斷句。")
            except Exception as ex:
                logger.warning(f"標點模型載入例外: {ex}")

    def _apply_ct_punc(self, text: str) -> str:
        """使用 CT-Transformer 獨立標點神經網路重建精準中文全形標點（，。！？、）"""
        if not text or not text.strip() or self.punc is None:
            return text
        try:
            plain = re.sub(r'[，。！？、；：,.!?;:]+', ' ', text).strip()
            plain = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', plain)
            if not plain:
                return text
            punc_res = self.punc(plain)
            if punc_res and len(punc_res) > 0 and punc_res[0]:
                return str(punc_res[0]).strip()
        except Exception as e:
            logger.warning(f"CT-Transformer 標點預測例外: {e}")
        return text

    def switch_engine(self, engine_name: str = "SenseVoice-Small") -> str:
        """v3.3 固定採用黃金模型 SenseVoice-Small"""
        self._load_sensevoice()
        return "SenseVoice-Small"

    def switch_model(self, model_name: str = "SenseVoice-Small") -> bool:
        """向下相容介面"""
        return self._load_sensevoice()

    def get_current_engine_name(self) -> str:
        return "SenseVoice-Small"

    def transcribe(
        self,
        audio_input: Union[str, np.ndarray],
        domain_terms: Optional[List[Union[str, dict]]] = None,
        language: str = "zh",
        hotwords: Optional[List[str]] = None
    ) -> TranscriptionResult:
        raw_text = ""
        backend_name = "SenseVoice-Small"
        audio_arr = self._load_audio(audio_input)
        if audio_arr is None or len(audio_arr) < 16000 * 0.2:
            return TranscriptionResult("", [], backend=backend_name)
        duration = round(len(audio_arr) / 16000.0, 2)

        if self.sensevoice_model is not None:
            try:
                res = self.sensevoice_model(audio_arr, language="auto", use_itn=True)
                if res and len(res) > 0:
                    raw_text = str(res[0])
                    raw_text = re.sub(r'<\|.*?\|>', '', raw_text).strip()
                if raw_text.strip() and self.punc is not None:
                    raw_text = self._apply_ct_punc(raw_text)
            except Exception as e:
                logger.error(f"SenseVoice 推論例外: {e}")

        if not raw_text.strip():
            return TranscriptionResult("", [], backend=backend_name)

        if _cc:
            raw_text = _cc.convert(raw_text)

        if raw_text and not re.search(r'[，。！？、,.!?]$', raw_text):
            raw_text += "。"

        return TranscriptionResult(
            raw_text.strip(),
            [{"start": 0.0, "end": duration, "text": raw_text.strip()}],
            backend=backend_name
        )

    def _load_audio(self, audio_input: Union[str, np.ndarray]) -> Optional[np.ndarray]:
        if isinstance(audio_input, np.ndarray):
            return audio_input
        if isinstance(audio_input, str) and os.path.exists(audio_input):
            try:
                import soundfile as sf
                data, sr = sf.read(audio_input)
                if data.ndim > 1:
                    data = data.mean(axis=1)
                if sr != 16000:
                    try:
                        import librosa
                        data = librosa.resample(data, orig_sr=sr, target_sr=16000)
                    except Exception:
                        pass
                return data.astype(np.float32)
            except Exception as e:
                logger.error(f"讀取音訊失敗: {e}")
                return None
        return None
