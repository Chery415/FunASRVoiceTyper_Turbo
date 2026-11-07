# 02. 輕量化程式碼完整改寫規格書 (v3.3 Lean Golden Edition Code Modification Guide)

請嚴格按照本規格書中的順序與完整程式碼，依序修改或覆寫以下 7 個核心檔案。
**注意**：所有程式碼皆為完整可執行版本，請直接使用 `write_file(..., Overwrite=True)` 完整替換，切勿自行刪減任何函式或相容別名。

---

## 一、 修改 `download_upgrade_models.py`（清理冗餘肥大模型並驗證 3 大輕量核心模型）

此腳本將負責：
1. 若 `models/qwen2.5-0.5b-instruct-q4_k_m.gguf` 已存在而 `models/llm/` 下尚未有該檔案，自動搬移至 `models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf`，避免重複下載或重複打包。
2. 自動刪除已淘汰的肥大模型目錄與檔案（`paraformer-large-onnx`、`faster-whisper-small`、`faster-whisper-turbo`、`qwen2.5-1.5b-instruct-q4_k_m.gguf`）以及測試產生的暫存檔（`temp_test_audio.wav`、`benchmark_18_*.py/.json`）。
3. 確認唯一黃金組合所需的 3 個模型（`SenseVoice-Small`、`CT-Transformer`、`Qwen2.5-0.5B`）完整就緒。

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\download_upgrade_models.py` 完整覆寫為：

```python
# coding: utf-8
"""
download_upgrade_models.py (v3.3 極致輕量化黃金組合版)
只保留並驗證 16/17/18 黃金組合所需之 3 個核心輕量離線模型：
1. 主力語音模型: SenseVoice-Small (ONNX INT8) -> models/sensevoice-small-onnx (~230 MB)
2. 獨立中文標點大模型: CT-Transformer (ONNX INT8) -> models/punc_ct-transformer_zh-cn-common-vocab272727-onnx (~278 MB)
3. 內嵌語意精校模型: Qwen2.5-0.5B-Instruct (GGUF Q4_K_M) -> models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf (~397 MB)
同時自動清理舊版冗餘之肥大模型 (Paraformer / Whisper / 1.5B GGUF) 與測試暫存檔。
"""

import os
import sys
import shutil
import json
import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from huggingface_hub import snapshot_download, hf_hub_download

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
SENSEVOICE_DIR = os.path.join(MODELS_DIR, "sensevoice-small-onnx")
PUNC_DIR = os.path.join(MODELS_DIR, "punc_ct-transformer_zh-cn-common-vocab272727-onnx")
LLM_DIR = os.path.join(MODELS_DIR, "llm")
TARGET_05B_NAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"


def _ensure_clean_real_dir(path: str):
    if os.path.lexists(path) and not os.path.exists(path):
        try:
            os.rmdir(path)
        except Exception:
            try:
                os.remove(path)
            except Exception:
                pass
    os.makedirs(path, exist_ok=True)


def _fix_punc_files(target_dir: str):
    """確保 CT-Transformer 具備 funasr_onnx 所需之 config.yaml (含 model_conf.punc_list) 與 tokens.json"""
    punc_yaml = os.path.join(target_dir, "punc.yaml")
    config_yaml = os.path.join(target_dir, "config.yaml")
    if os.path.exists(punc_yaml):
        with open(punc_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if "model_conf" not in data:
            data["model_conf"] = {}
        data["model_conf"]["punc_list"] = data.get("punc_list", ['<unk>', '_', ',', '。', '?', '、'])
        with open(config_yaml, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    tok_txt = os.path.join(target_dir, "tokens.txt")
    tok_json = os.path.join(target_dir, "tokens.json")
    if os.path.exists(tok_txt) and not os.path.exists(tok_json):
        with open(tok_txt, "r", encoding="utf-8") as f:
            tokens = [line.strip("\r\n") for line in f]
        with open(tok_json, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False)


def cleanup_redundant_models_and_temp():
    """清理不再使用的肥大模型與測試暫存檔，達成極致輕量化部署"""
    print("=" * 68)
    print(" [Step 1] 正在清理冗餘模型與測試暫存檔案 (v3.3 瘦身工程)...")
    print("=" * 68)
    os.makedirs(LLM_DIR, exist_ok=True)

    # 若根目錄 models/ 下有 0.5B GGUF 但 models/llm/ 下沒有，先搬移過去避免重抓
    root_05b = os.path.join(MODELS_DIR, TARGET_05B_NAME)
    llm_05b = os.path.join(LLM_DIR, TARGET_05B_NAME)
    if os.path.exists(root_05b):
        if not os.path.exists(llm_05b):
            print(f"  -> 搬移 {root_05b} 至 {llm_05b}")
            shutil.move(root_05b, llm_05b)
        else:
            print(f"  -> 移除重複的根目錄模型檔: {root_05b}")
            try:
                os.remove(root_05b)
            except Exception as e:
                print(f"     移除失敗: {e}")

    # 要刪除的冗餘模型目錄
    obsolete_dirs = [
        os.path.join(MODELS_DIR, "paraformer-large-onnx"),
        os.path.join(MODELS_DIR, "faster-whisper-small"),
        os.path.join(MODELS_DIR, "faster-whisper-turbo"),
    ]
    for d in obsolete_dirs:
        if os.path.lexists(d):
            print(f"  -> 刪除已淘汰模型目錄: {d}")
            try:
                import stat
                def _remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                if os.path.islink(d) or not os.path.isdir(d):
                    os.chmod(d, stat.S_IWRITE)
                    os.remove(d)
                else:
                    os.chmod(d, stat.S_IWRITE)
                    shutil.rmtree(d, onerror=_remove_readonly)
            except Exception as e:
                print(f"     刪除目錄例外: {e}")

    # 要刪除的冗餘單一檔案與暫存檔
    obsolete_files = [
        os.path.join(MODELS_DIR, "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        os.path.join(LLM_DIR, "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        os.path.join(BASE_DIR, "temp_test_audio.wav"),
        os.path.join(BASE_DIR, "benchmark_18_modes.py"),
        os.path.join(BASE_DIR, "benchmark_18_results.json"),
        os.path.join(BASE_DIR, "benchmark_18_results_full.json"),
        os.path.join(BASE_DIR, "test_v32_asr_and_punc.py"),
    ]
    for fpath in obsolete_files:
        if os.path.exists(fpath):
            print(f"  -> 刪除冗餘檔案: {fpath}")
            try:
                os.remove(fpath)
            except Exception as e:
                print(f"     刪除檔案例外: {e}")

    print("✓ 冗餘模型與暫存檔清理完成！\n")


def download_and_verify_lean_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    _ensure_clean_real_dir(SENSEVOICE_DIR)
    _ensure_clean_real_dir(PUNC_DIR)
    _ensure_clean_real_dir(LLM_DIR)

    cleanup_redundant_models_and_temp()

    # 1. 驗證 SenseVoice-Small 主語音模型
    sv_quant = os.path.join(SENSEVOICE_DIR, "model_quant.onnx")
    if os.path.exists(sv_quant) and os.path.getsize(sv_quant) > 50 * 1024 * 1024:
        print(f"✓ [1/3] SenseVoice-Small 語音模型已就緒: {sv_quant}")
    else:
        print("正在下載 SenseVoice-Small (ONNX INT8)...")
        snapshot_download(
            repo_id="manyeyes/SenseVoiceSmall-onnx",
            local_dir=SENSEVOICE_DIR,
            ignore_patterns=["*.md", ".gitattributes"]
        )
        print(f"✓ [1/3] SenseVoice-Small 下載完成: {SENSEVOICE_DIR}")

    # 2. 驗證 CT-Transformer 27萬詞表中文標點模型
    punc_quant = os.path.join(PUNC_DIR, "model_quant.onnx")
    if os.path.exists(punc_quant) and os.path.getsize(punc_quant) > 50 * 1024 * 1024:
        print(f"✓ [2/3] CT-Transformer 標點大模型已就緒: {punc_quant}")
    else:
        print("正在下載 CT-Transformer 標點大模型 (ONNX INT8)...")
        snapshot_download(
            repo_id="manyeyes/punc_ct-transformer_zh-cn-common-vocab272727-onnx",
            local_dir=PUNC_DIR,
            ignore_patterns=["model.onnx", "*.md", ".gitattributes", "example/*", "fig/*"]
        )
    _fix_punc_files(PUNC_DIR)

    # 3. 驗證 Qwen2.5-0.5B-Instruct 極速語意模型
    target_05b = os.path.join(LLM_DIR, TARGET_05B_NAME)
    if os.path.exists(target_05b) and os.path.getsize(target_05b) > 100 * 1024 * 1024:
        print(f"✓ [3/3] Qwen2.5-0.5B-Instruct GGUF 語意模型已就緒: {target_05b}")
    else:
        print(f"正在下載 Qwen2.5-0.5B-Instruct ({TARGET_05B_NAME})...")
        hf_hub_download(
            repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
            filename=TARGET_05B_NAME,
            local_dir=LLM_DIR
        )
        print(f"✓ [3/3] Qwen2.5-0.5B-Instruct 下載完成: {target_05b}")

    print("\n🎉 FunASRVoiceTyper_Turbo v3.3 黃金輕量版模型瘦身與檢核 100% 完成！")


if __name__ == "__main__":
    download_and_verify_lean_models()
```

---

## 二、 修改 `config.json`（鎖定 SenseVoice-Small + Qwen2.5-0.5B 黃金配置）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\config.json` 完整覆寫為：

```json
{
  "hotkey": "right ctrl",
  "language": "zh",
  "asr_model_id": "SenseVoice-Small",
  "llm_backend": "embedded",
  "llm_gguf_path": "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf",
  "llm_api_base": "http://localhost:11434/v1",
  "llm_model_name": "qwen2.5:0.5b-instruct-q4_K_M",
  "llm_api_key": "",
  "domain_terms": [
    "台積電",
    "CoWoS",
    "EUV",
    "先進製程",
    "晶圓代工",
    "半導體",
    "AI",
    "API",
    "Agent",
    "Meeting",
    "GitHub",
    "SFTPGo",
    "Windows",
    "Ubuntu",
    "Ubuntu Server",
    "Linux",
    "Google Antigravity",
    "Antigravity",
    "Claude Code",
    "Gemini",
    "Flash",
    "Pro",
    "Token",
    "迷你PC",
    "指令碼",
    "程式碼",
    "測試檔案",
    "測試案例",
    "資訊安全",
    "資安工具",
    "資安長",
    "資安",
    "模型",
    "大竹國小",
    "韓風熱舞社",
    "標點符號",
    "語音辨識",
    "辨識速度",
    "工作執行說明書",
    "城市=>程式",
    "層次碼=>程式碼",
    "程試碼=>程式碼",
    "測試碼=>程式碼",
    "測型檔案=>測試檔案",
    "測行檔案=>測試檔案",
    "測告=>測試",
    "裡麵=>裡面",
    "治安=>資安",
    "自然工具=>資安工具",
    "自然長=>資安長",
    "辨試=>辨識",
    "變試=>辨識",
    "面試的速度=>辨識的速度",
    "變化的速度=>辨識的速度",
    "連點符號=>標點符號",
    "語役分析=>語意分析",
    "大竹郭小=>大竹國小",
    "大主播小=>大竹國小",
    "寒風熱舞室=>韓風熱舞社",
    "寒風熱舞社=>韓風熱舞社",
    "gmin=>Gemini",
    "germin=>Gemini",
    "german=>Gemini",
    "integravity=>Antigravity",
    "cloucoo=>Claude Code",
    "claucoo=>Claude Code",
    "reno 4=>Linux"
  ],
  "enable_correction": true,
  "min_llm_char_length": 2,
  "llm_timeout_seconds": 6.0,
  "typeless_timeout_seconds": 10.0,
  "typing_mode": "typeless",
  "auto_start": false
}
```

---

## 三、 修改 `core/domain_normalizer.py`（補充實測同音字內建映射，強化組合 16 Instant 模式零錯字能力）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\core\domain_normalizer.py` 完整覆寫為：

```python
"""
DomainTermsNormalizer: 本機高效專有名詞、同音字與口語贅字清洗引擎 (v3.3 黃金輕量版)
具備零外連、零延遲 (< 0.5ms) 特性：
1. 提供聲學熱詞 (Hotwords) 萃取。
2. 強化口語結巴、助詞疊字（的的）、半截重複片語（把A把B）與填充贅詞過濾。
3. 顯式別名映射與繁體中文模糊拼音（平翹舌/前後鼻音）同音校正，確保 Instant (0ms LLM) 模式同樣具備高專業詞準度。
"""

import re
import logging
from typing import List, Dict, Union, Tuple, Optional

try:
    import pypinyin
    _HAS_PYPINYIN = True
except ImportError:
    _HAS_PYPINYIN = False

logger = logging.getLogger("DomainTermsNormalizer")

BUILTIN_MAPPINGS = {
    "因該": "應該",
    "在次": "再次",
    "在度": "再度",
    "決對": "絕對",
    "既使": "即使",
    "以經": "已經",
    "在見": "再見",
    "部份": "部分",
    "裡麵": "裡面",
    "辨試": "辨識",
    "變試": "辨識",
    "面試的速度": "辨識的速度",
    "變化的速度": "辨識的速度",
    "連點符號": "標點符號",
    "語役分析": "語意分析",
    "大竹郭小": "大竹國小",
    "大主播小": "大竹國小",
    "寒風熱舞室": "韓風熱舞社",
    "寒風熱舞社": "韓風熱舞社",
    "gmin": "Gemini",
    "germin": "Gemini",
    "german": "Gemini",
    "integravity": "Antigravity",
    "cloucoo": "Claude Code",
    "claucoo": "Claude Code",
    "層次碼": "程式碼",
    "程試碼": "程式碼",
    "測試碼": "程式碼",
    "測型檔案": "測試檔案",
    "測行檔案": "測試檔案",
    "進行測告": "進行測試",
    "這試的工具": "這些工具",
    "每個別針對": "個別針對",
    "最生一份": "最後產生一份",
}


def _get_fuzzy_pinyin(chars: str) -> Tuple[str, ...]:
    if not _HAS_PYPINYIN or not chars:
        return ()
    try:
        py_list = pypinyin.lazy_pinyin(chars)
        res = []
        for p in py_list:
            p_clean = p.lower()
            if p_clean.startswith('zh'):
                p_clean = 'z' + p_clean[2:]
            elif p_clean.startswith('ch'):
                p_clean = 'c' + p_clean[2:]
            elif p_clean.startswith('sh'):
                p_clean = 's' + p_clean[2:]

            if p_clean.endswith('ing'):
                p_clean = p_clean[:-3] + 'in'
            elif p_clean.endswith('eng'):
                p_clean = p_clean[:-3] + 'en'
            res.append(p_clean)
        return tuple(res)
    except Exception:
        return ()


def extract_hotwords_list(domain_terms: Optional[List[Union[str, Dict[str, str]]]]) -> List[str]:
    if not domain_terms:
        return []
    out: List[str] = []
    for item in domain_terms:
        if isinstance(item, dict):
            for v in item.values():
                val = str(v).strip()
                if val:
                    out.append(val)
        elif isinstance(item, str):
            s = item.strip()
            if not s or s.startswith(("#", "//")):
                continue
            parts = re.split(r'=>|->', s, maxsplit=1)
            target = parts[-1].strip()
            if target:
                out.append(target)
    seen = set()
    uniq = []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


class DomainTermsNormalizer:
    def __init__(self, domain_terms: Optional[List[Union[str, Dict[str, str]]]] = None):
        self.mapping_rules: Dict[str, str] = BUILTIN_MAPPINGS.copy()
        self.canonical_terms: List[str] = []
        self.english_terms: List[Tuple[str, re.Pattern]] = []
        self.chinese_terms: List[Tuple[str, int, Tuple[str, ...]]] = []
        if domain_terms:
            self.load_terms(domain_terms)

    def load_terms(self, domain_terms: List[Union[str, Dict[str, str]]]):
        for item in domain_terms:
            if isinstance(item, dict):
                for k, v in item.items():
                    k_clean = str(k).strip()
                    v_clean = str(v).strip()
                    if k_clean and v_clean:
                        self.mapping_rules[k_clean] = v_clean
            elif isinstance(item, str):
                s = item.strip()
                if not s or s.startswith("//") or s.startswith("#"):
                    continue
                if "=>" in s:
                    parts = s.split("=>", 1)
                    self.mapping_rules[parts[0].strip()] = parts[1].strip()
                    self.canonical_terms.append(parts[1].strip())
                elif "->" in s:
                    parts = s.split("->", 1)
                    self.mapping_rules[parts[0].strip()] = parts[1].strip()
                    self.canonical_terms.append(parts[1].strip())
                elif ":" in s and not s.startswith("http"):
                    parts = s.split(":", 1)
                    self.mapping_rules[parts[0].strip()] = parts[1].strip()
                    self.canonical_terms.append(parts[1].strip())
                else:
                    self.canonical_terms.append(s)

        for term in self.canonical_terms:
            if re.search(r'[a-zA-Z]', term):
                pattern = re.compile(
                    r'(?<![a-zA-Z0-9])' + re.escape(term) + r'(?![a-zA-Z0-9])',
                    re.IGNORECASE
                )
                self.english_terms.append((term, pattern))

        chinese_list = [
            t for t in self.canonical_terms
            if re.search(r'[\u4e00-\u9fff]', t) and len(t) >= 2
        ]
        chinese_list.sort(key=lambda x: len(x), reverse=True)

        for term in chinese_list:
            t_len = len(term)
            fuzzy_py = _get_fuzzy_pinyin(term)
            if fuzzy_py:
                self.chinese_terms.append((term, t_len, fuzzy_py))

    def _remove_stutters(self, text: str) -> str:
        text = re.sub(r'([的了得過著])\1+', r'\1', text)
        text = re.sub(r'([我你他她它這那就把被對在從跟和與])\1+', r'\1', text)
        text = re.sub(r'把[\u4e00-\u9fff]{1,3}把(?=[\u4e00-\u9fff]{2,})', '把', text)
        text = re.sub(r'對[\u4e00-\u9fff]{1,2}對(?=[\u4e00-\u9fff]{2,})', '對', text)

        for w in ['然後', '那個', '這個', '就是說', '就是', '所以', '因為', '可能', '我們', '我覺得', '其實', '那其實']:
            text = re.sub(rf'(?:{w}[，、\s]*){{2,}}', w, text)

        text = re.sub(r'(^|[，。！？、\s])(?:呃+|嗯+|欸+|啊那個|呃那個|嗯那個)[，、\s]*', r'\1', text)
        text = re.sub(r'([，。！？、])\1+', r'\1', text)
        return text.strip()

    def normalize(self, text: str) -> str:
        if not text:
            return text

        text = self._remove_stutters(text)

        sorted_mappings = sorted(self.mapping_rules.items(), key=lambda x: len(x[0]), reverse=True)
        for src, dst in sorted_mappings:
            if re.search(r'[a-zA-Z]', src):
                text = re.sub(re.escape(src), dst, text, flags=re.IGNORECASE)
            elif src in text:
                text = text.replace(src, dst)

        for orig_term, pattern in self.english_terms:
            text = pattern.sub(orig_term, text)

        if _HAS_PYPINYIN and self.chinese_terms:
            chars = list(text)
            n_chars = len(chars)
            for target_term, t_len, term_fuzzy in self.chinese_terms:
                if t_len > n_chars:
                    continue
                i = 0
                while i <= len(chars) - t_len:
                    sub_str = ''.join(chars[i:i + t_len])
                    if sub_str == target_term:
                        i += t_len
                        continue
                    if all('\u4e00' <= c <= '\u9fff' for c in sub_str):
                        sub_fuzzy = _get_fuzzy_pinyin(sub_str)
                        if sub_fuzzy == term_fuzzy:
                            chars[i:i + t_len] = list(target_term)
                            i += t_len
                            continue
                    i += 1
                text = ''.join(chars)

        text = self._remove_stutters(text)
        return text


def normalize_domain_terms(text: str, domain_terms: Optional[List[Union[str, Dict[str, str]]]]) -> str:
    if not text:
        return text
    normalizer = DomainTermsNormalizer(domain_terms)
    return normalizer.normalize(text)


DomainNormalizer = DomainTermsNormalizer
```

---

## 四、 修改 `core/asr_engine.py`（專注於 `SenseVoice-Small` + `CT-Transformer` 標點大模型，徹底移除 Paraformer 與 Whisper 依賴）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\core\asr_engine.py` 完整覆寫為：

```python
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
```

---

## 五、 修改 `core/llm_client.py`（專注於內嵌 `Qwen2.5-0.5B-Instruct` 極速語意模型）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\core\llm_client.py` 完整覆寫為：

```python
"""
SPEECH-PIPELINE-HYBRID-FAST: 本地 LLM 語意重構與同音糾錯引擎 (v3.3 黃金輕量版)
專注於實測速度與性價比第一名之 Qwen2.5-0.5B-Instruct (Q4_K_M)：
1. 透過 llama-cpp-python 於進程記憶體內直接推論 (In-Process Inference)。
2. 分離 n_threads (實體核心數) 與 n_threads_batch (全邏輯執行緒)。
3. 開機預熱直接鎖定 UNIFIED_SYSTEM_PROMPT 的 KV Prefix Cache，切換模式零延遲。
"""

import os
import sys
import re
import json
import glob
import logging
import time
import socket
import threading
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Tuple, List

from core.prompt import UNIFIED_SYSTEM_PROMPT

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
        self.backend = (backend or "embedded").lower()
        self.gguf_path = gguf_path
        self.resolved_gguf_path: Optional[str] = None
        self._llama = None
        self._lock = threading.Lock()

        self.api_base = (api_base or "http://localhost:11434/v1").rstrip("/")
        self.model_name = model_name
        self.api_key = (api_key or "").strip()
        self.chat_endpoint = f"{self.api_base}/chat/completions"
        self._last_online_check = 0.0
        self._cached_online_status = False

        if self.backend == "embedded":
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
            gen_threads = max(2, min(4, logical_cpus // 2))
            batch_threads = max(4, min(8, logical_cpus))
            logger.info(
                f"正在載入內嵌 GGUF 語意重構模型 (gen_threads={gen_threads}, batch_threads={batch_threads}): {gguf_file}"
            )
            self._llama = Llama(
                model_path=gguf_file,
                n_ctx=1024,
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

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def warmup(self, timeout_seconds: float = 60.0) -> bool:
        """預熱模型並將 UNIFIED_SYSTEM_PROMPT 預先鎖入 llama.cpp 的 KV Prefix Cache"""
        if self.backend == "embedded":
            if self._llama is None and not self._init_embedded_llama():
                return False
            try:
                t0 = time.perf_counter()
                with self._lock:
                    self._llama.create_chat_completion(
                        messages=[
                            {"role": "system", "content": UNIFIED_SYSTEM_PROMPT},
                            {"role": "user", "content": "請修正以下語音草稿中的同音錯別字並補齊正確的全形逗號與句號：\n測試預熱。"}
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

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": "ok"}],
            "max_tokens": 1,
            "stream": False,
            "keep_alive": "60m",
        }
        try:
            req = urllib.request.Request(
                self.chat_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers()
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"HTTP LLM 預熱失敗: {e}")
            return False

    def is_online(self, cache_ttl: float = 4.0) -> bool:
        if self.backend == "embedded":
            return self._llama is not None

        now = time.perf_counter()
        if (now - self._last_online_check) < cache_ttl:
            return self._cached_online_status

        self._last_online_check = now
        try:
            parsed = urllib.parse.urlparse(self.api_base)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.08)
            res = sock.connect_ex((host, port))
            sock.close()
            self._cached_online_status = (res == 0)
        except Exception:
            self._cached_online_status = False

        return self._cached_online_status

    def correct_text(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float = 8.0
    ) -> Tuple[Optional[str], float, bool]:
        if not self.is_online():
            return None, 0.0, False

        t_start = time.perf_counter()

        if self.backend == "embedded" and self._llama is not None:
            try:
                max_tok = max(48, min(512, int(len(user_prompt) * 1.6) + 24))
                with self._lock:
                    resp = self._llama.create_chat_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1,
                        top_p=0.9,
                        repeat_penalty=1.12,
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

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "stream": False,
            "max_tokens": max(64, min(1024, int(len(user_prompt) * 1.8))),
            "keep_alive": "60m"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.chat_endpoint,
            data=data,
            headers=self._headers()
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                if resp.status == 200:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    content = resp_data["choices"][0]["message"]["content"].strip()
                    cleaned = self._clean_llm_output(content)
                    return cleaned, elapsed_ms, bool(cleaned)
                return None, elapsed_ms, False
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            logger.warning(f"LLM API 請求失敗或逾時: {e} (耗時: {elapsed_ms:.1f}ms)")
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
```

---

## 六、 修改 `core/pipeline.py`（固定為 SenseVoice-Small + Qwen2.5-0.5B 黃金管線）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\core\pipeline.py` 完整覆寫為：

```python
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
```

---

## 七、 修改 `main.py`（精簡系統托盤選單：僅保留組合 16、17、18 的打字模式切換與核心設定）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\main.py` 完整覆寫為：

```python
"""
FunASRVoiceTyper_Turbo v3.3 (Lean Golden Edition):
專注於實測綜合表現最佳之黃金組合 (組合 16 / 17 / 18)：
- 語音與標點引擎：固定採用 SenseVoice-Small (ONNX) + CT-Transformer 標點大模型
- 語意重構引擎：固定採用內嵌 Qwen2.5-0.5B-Instruct (GGUF)
- 系統托盤選單：移除多餘的模型切換子選單，僅保留核心 3 種打字模式 (Instant / Typeless / Structured) 與系統設定
"""

import os
import sys
import json
import ctypes
import tempfile
import threading
import subprocess
from PIL import Image, ImageDraw
import pystray
import soundfile as sf

import logging
from core.autostart import is_auto_start_enabled, set_auto_start
from core.audio_recorder import AudioRecorder
from core.pipeline import HybridSpeechPipeline
from core.text_injector import TextInjector
from core.hotkey_listener import ToggleVoiceController
from core.wave_overlay import WaveOverlay

CONFIG_FILENAME = "config.json"
_SINGLE_INSTANCE_MUTEX = None


def acquire_single_instance_lock() -> bool:
    global _SINGLE_INSTANCE_MUTEX
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\FunASRVoiceTyper_Turbo_SingleInstance_Mutex_v3"
        handle = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == 183:
            return False
        _SINGLE_INSTANCE_MUTEX = handle
        return True
    except Exception:
        return True


def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.join(get_app_dir(), CONFIG_FILENAME)


def setup_logging():
    log_file = os.path.join(get_app_dir(), "app.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
        force=True
    )
    logging.info("==========================================")
    logging.info("  FunASRVoiceTyper_Turbo v3.3 黃金輕量版日誌已啟動")
    logging.info("==========================================")

    class StdoutRedirector:
        def __init__(self, logger_func, stream=None):
            self.logger_func = logger_func
            self.stream = stream
            self.buf = ""

        def write(self, s):
            if self.stream:
                try:
                    self.stream.write(s)
                except Exception:
                    pass
            self.buf += s
            if "\n" in self.buf:
                parts = self.buf.split("\n")
                for p in parts[:-1]:
                    if p.strip():
                        self.logger_func(p)
                self.buf = parts[-1]

        def flush(self):
            if self.stream:
                try:
                    self.stream.flush()
                except Exception:
                    pass
            if self.buf.strip():
                self.logger_func(self.buf)
                self.buf = ""

    sys.stdout = StdoutRedirector(logging.info, sys.stdout)
    sys.stderr = StdoutRedirector(logging.error, sys.stderr)


setup_logging()


def load_config() -> dict:
    cfg_path = get_config_path()
    default_cfg = {
        "hotkey": "right ctrl",
        "language": "zh",
        "asr_model_id": "SenseVoice-Small",
        "llm_backend": "embedded",
        "llm_gguf_path": "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "llm_api_base": "http://localhost:11434/v1",
        "llm_model_name": "qwen2.5:0.5b-instruct-q4_K_M",
        "llm_api_key": "",
        "domain_terms": [
            "台積電", "CoWoS", "EUV", "先進製程", "晶圓代工", "半導體",
            "AI", "API", "Agent", "Meeting", "GitHub", "SFTPGo",
            "Windows", "Ubuntu", "Linux", "Google Antigravity", "Antigravity",
            "Claude Code", "Gemini", "指令碼", "程式碼", "測試檔案", "資安工具", "資安", "模型",
            "大竹國小", "韓風熱舞社", "標點符號", "語音辨識", "辨識速度",
            "城市=>程式", "層次碼=>程式碼", "程試碼=>程式碼", "測試碼=>程式碼",
            "測型檔案=>測試檔案", "測行檔案=>測試檔案", "測告=>測試", "裡麵=>裡面",
            "治安=>資安", "辨試=>辨識", "變試=>辨識", "面試的速度=>辨識的速度",
            "大竹郭小=>大竹國小", "大主播小=>大竹國小", "寒風熱舞室=>韓風熱舞社",
            "gmin=>Gemini", "integravity=>Antigravity", "cloucoo=>Claude Code", "reno 4=>Linux"
        ],
        "enable_correction": True,
        "min_llm_char_length": 2,
        "llm_timeout_seconds": 6.0,
        "typeless_timeout_seconds": 10.0,
        "typing_mode": "typeless",
        "auto_start": False
    }
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8-sig") as f:
            json.dump(default_cfg, f, indent=2, ensure_ascii=False)
        return default_cfg
    try:
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            for k, v in default_cfg.items():
                if k not in data:
                    data[k] = v
            data["asr_model_id"] = "SenseVoice-Small"
            data["llm_gguf_path"] = "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
            return data
    except Exception:
        return default_cfg


def save_config(cfg: dict):
    cfg_path = get_config_path()
    with open(cfg_path, "w", encoding="utf-8-sig") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def create_tray_icon(primary_color: str, text: str = "FT") -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 60, 60), fill=primary_color)
    draw.ellipse((14, 14, 50, 50), fill=(22, 18, 30, 230))
    draw.text((22, 23), text, fill=primary_color)
    return image


class HybridVoiceTyperApp:
    def __init__(self):
        logging.info("初始化 HybridVoiceTyperApp v3.3 (黃金輕量版)...")
        self.config = load_config()
        self.recorder = AudioRecorder()
        self.injector = TextInjector()
        self.wave_overlay = WaveOverlay(get_level_func=self.recorder.get_volume)

        self.idle_icon = create_tray_icon("#0284C7", "FT")
        self.loading_icon = create_tray_icon("#888888", "...")
        self.recording_icon = create_tray_icon("#FF3B30", "REC")
        self.error_icon = create_tray_icon("#E11D48", "ERR")

        self.is_model_ready = False
        self.pipeline = None
        self.is_processing = False
        self.controller = None
        self.tray_icon = None
        self._init_controller()

        threading.Thread(target=self._load_pipeline_async, daemon=True).start()

    def _load_pipeline_async(self):
        print("[HybridApp] 正在背景非同步預載入 SenseVoice-Small、CT-Transformer 標點與 Qwen2.5-0.5B 引擎...")
        try:
            self.pipeline = HybridSpeechPipeline(
                asr_model_id="SenseVoice-Small",
                llm_api_base=self.config.get("llm_api_base", "http://localhost:11434/v1"),
                llm_model_name="qwen2.5:0.5b-instruct-q4_K_M",
                device="cpu",
                llm_api_key=self.config.get("llm_api_key", ""),
                llm_backend=self.config.get("llm_backend", "embedded"),
                llm_gguf_path="models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf"
            )
            if self.pipeline.is_llm_online():
                self.pipeline.warmup_llm()
            else:
                logging.warning("[HybridApp] ⚠️ LLM 引擎未就緒，將僅使用 SenseVoice + CT標點 + Layer 1.5 規則校正。")

            self.is_model_ready = True
            print("[HybridApp] SenseVoice-Small + CT標點 + Qwen2.5-0.5B 黃金組合載入就緒！")
            try:
                import winsound
                winsound.Beep(1200, 100)
            except Exception:
                pass
            self.update_tray(recording=False)
            if self.tray_icon:
                try:
                    self.tray_icon.update_menu()
                except Exception:
                    pass
        except Exception as e:
            import traceback
            err_msg = f"[HybridApp] 引擎載入錯誤: {e}\n{traceback.format_exc()}"
            print(err_msg)
            logging.error(err_msg)
            if self.tray_icon:
                self.tray_icon.icon = self.error_icon
                self.tray_icon.title = f"SpeechPipeline [載入錯誤: {e}]"

    def _init_controller(self):
        current_hotkey = self.config.get("hotkey", "right ctrl")
        self.controller = ToggleVoiceController(
            hotkey=current_hotkey,
            on_start=self.on_start_recording,
            on_stop=self.on_stop_recording
        )

    def reload_config_if_modified(self):
        cfg_path = get_config_path()
        try:
            if os.path.exists(cfg_path):
                mtime = os.path.getmtime(cfg_path)
                if not hasattr(self, '_last_cfg_mtime') or mtime > self._last_cfg_mtime:
                    self._last_cfg_mtime = mtime
                    fresh_cfg = load_config()
                    old_hotkey = self.config.get("hotkey", "").lower()
                    new_hotkey = fresh_cfg.get("hotkey", "").lower()
                    self.config = fresh_cfg
                    if old_hotkey != new_hotkey and self.controller:
                        logging.info(f"[Config] 偵測到熱鍵更新: {old_hotkey} -> {new_hotkey}")
                        self.change_hotkey(new_hotkey)
                    terms_count = len(self.config.get("domain_terms", []))
                    logging.info(f"[Config] 已即時動態載入最新設定！自訂專有名詞數量: {terms_count}")
        except Exception as e:
            logging.error(f"[Config] 動態讀取設定檔例外: {e}")

    def on_start_recording(self):
        self.reload_config_if_modified()
        if not self.is_model_ready:
            print("[HybridApp] ⚠️ 語音模型仍在載入與預熱中，請稍候 1~2 秒...")
            try:
                import winsound
                winsound.Beep(400, 150)
            except Exception:
                pass
            return

        print("\n[HybridApp] 🔴 開始錄音...")
        self.update_tray(recording=True)
        self.wave_overlay.show_recording()
        self.recorder.start()

    def on_stop_recording(self):
        self.reload_config_if_modified()
        print("[HybridApp] ⏹️ 停止錄音，轉錄與標點精校中...")
        self.wave_overlay.show_processing()
        self.update_tray(recording=False)
        audio = self.recorder.stop()

        def _worker():
            self.is_processing = True
            temp_wav_path = None
            try:
                if len(audio) < 16000 * 0.2:
                    print("[HybridApp] ⚠️ 音訊過短")
                    self.wave_overlay.hide()
                    return

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    temp_wav_path = tmp.name
                    sf.write(temp_wav_path, audio, 16000)

                self.reload_config_if_modified()
                domain_terms = self.config.get("domain_terms", [])
                enable_correction = self.config.get("enable_correction", True)
                typing_mode = self.config.get("typing_mode", "typeless")
                min_llm_len = int(self.config.get("min_llm_char_length", 2))

                if typing_mode in ("typeless", "structured"):
                    llm_timeout_seconds = float(self.config.get("typeless_timeout_seconds", 10.0))
                else:
                    llm_timeout_seconds = float(self.config.get("llm_timeout_seconds", 6.0))

                res = self.pipeline.process(
                    audio_path=temp_wav_path,
                    domain_terms=domain_terms,
                    enable_correction=enable_correction,
                    llm_timeout_seconds=llm_timeout_seconds,
                    typing_mode=typing_mode,
                    min_llm_char_length=min_llm_len
                )

                if res.final_text:
                    fallback_info = " (規則備援)" if res.is_fallback else ""
                    print(
                        f"[HybridApp] ✓ 轉錄完成 [ASR:{res.asr_latency_ms:.1f}ms, "
                        f"LLM:{res.llm_latency_ms:.1f}ms, 總計:{res.total_latency_ms:.1f}ms{fallback_info}]: "
                        f"{res.final_text}"
                    )
                    self.injector.inject_text(res.final_text)
                    self.wave_overlay.show_success(duration_ms=350)
                else:
                    print("[HybridApp] ⚠️ 未辨識出有效文字")
                    self.wave_overlay.hide()
            except Exception as e:
                print(f"[HybridApp] ❌ 處理錯誤: {e}")
                self.wave_overlay.hide()
            finally:
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.remove(temp_wav_path)
                    except Exception:
                        pass
                self.is_processing = False

        threading.Thread(target=_worker, daemon=True).start()

    def update_tray(self, recording: bool):
        if self.tray_icon:
            hotkey_name = self.config.get('hotkey', 'right ctrl').upper()
            mode_label = self.config.get('typing_mode', 'typeless')
            if not self.is_model_ready:
                self.tray_icon.icon = self.loading_icon
                self.tray_icon.title = "FunASRVoiceTyper Turbo (模型載入預熱中...)"
            else:
                self.tray_icon.icon = self.recording_icon if recording else self.idle_icon
                title = (
                    "FunASRVoiceTyper Turbo (錄音中...)"
                    if recording
                    else f"FunASRVoiceTyper Turbo (SenseVoice+0.5B | {mode_label} | 熱鍵: {hotkey_name})"
                )
                self.tray_icon.title = title

    def change_typing_mode(self, mode_name: str):
        try:
            self.reload_config_if_modified()
            self.config["typing_mode"] = mode_name
            save_config(self.config)
            print(f"[HybridApp] ✓ 打字模式切換成功: {mode_name} (KV Cache 保持常駐不失效)")
            self.update_tray(recording=False)
            if self.tray_icon:
                self.tray_icon.update_menu()
        except Exception as e:
            print(f"[HybridApp] 切換打字模式失敗: {e}")

    def change_hotkey(self, new_hotkey: str):
        try:
            self.controller.stop_listening()
            self.reload_config_if_modified()
            self.config["hotkey"] = new_hotkey
            save_config(self.config)
            self._init_controller()
            self.controller.start_listening()
            self.update_tray(recording=False)
            if self.tray_icon:
                self.tray_icon.update_menu()
            print(f"[HybridApp] 熱鍵已更新為: {new_hotkey}")
        except Exception as e:
            print(f"[HybridApp] 更新熱鍵失敗: {e}")

    def toggle_autostart(self, icon, item):
        current = is_auto_start_enabled()
        new_state = not current
        set_auto_start(new_state)
        self.config["auto_start"] = new_state
        save_config(self.config)
        icon.update_menu()

    def open_config(self, icon, item):
        cfg_path = get_config_path()
        try:
            os.startfile(cfg_path)
        except Exception:
            subprocess.run(["notepad.exe", cfg_path])

    def exit_app(self, icon, item):
        print("[HybridApp] 正在退出程式...")
        self.controller.stop_listening()
        self.wave_overlay.hide()
        icon.stop()

    def _is_llm_online(self) -> bool:
        if self.pipeline is not None:
            return self.pipeline.is_llm_online()
        return False

    def run(self):
        self.controller.start_listening()

        def make_setter(key_name):
            return lambda icon, item: self.change_hotkey(key_name)

        def is_current(key_name):
            return lambda item: self.config.get("hotkey", "").lower() == key_name.lower()

        def make_mode_setter(mode_val):
            return lambda icon, item: self.change_typing_mode(mode_val)

        def is_mode_current(mode_val):
            return lambda item: self.config.get("typing_mode", "typeless").lower() == mode_val.lower()

        def get_engine_status_text(item):
            online = self._is_llm_online()
            if online and self.pipeline:
                return "🟢 黃金引擎在線 (SenseVoice-Small + CT標點 + Qwen2.5-0.5B)"
            return "⚪ 引擎載入中或僅用本機規則"

        menu = pystray.Menu(
            pystray.MenuItem(get_engine_status_text, lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "打字與段落重編模式 (Typing Mode)",
                pystray.Menu(
                    pystray.MenuItem(
                        "🟢 極速打字模式 (Instant - 0ms免LLM・即時標點上屏) [組合16]",
                        make_mode_setter("instant"),
                        checked=is_mode_current("instant"),
                        radio=True
                    ),
                    pystray.MenuItem(
                        "🟣 流暢修訂與同音精校 (Typeless - 0.5B極速修錯字/潤飾 - 推薦) [組合17]",
                        make_mode_setter("typeless"),
                        checked=is_mode_current("typeless"),
                        radio=True
                    ),
                    pystray.MenuItem(
                        "🔵 結構化闡述與指令模式 (Structured - 長篇重組為條理重點) [組合18]",
                        make_mode_setter("structured"),
                        checked=is_mode_current("structured"),
                        radio=True
                    )
                )
            ),
            pystray.MenuItem(
                "快速鍵設定 (Hotkey)",
                pystray.Menu(
                    pystray.MenuItem("右側 Ctrl (Right Ctrl - 推薦)", make_setter("right ctrl"), checked=is_current("right ctrl"), radio=True),
                    pystray.MenuItem("右側 Alt (Right Alt)", make_setter("right alt"), checked=is_current("right alt"), radio=True),
                    pystray.MenuItem("F8 鍵", make_setter("f8"), checked=is_current("f8"), radio=True),
                    pystray.MenuItem("開啟設定檔手動自訂...", self.open_config)
                )
            ),
            pystray.MenuItem(
                "開機自動啟動 (Start on Boot)",
                self.toggle_autostart,
                checked=lambda item: is_auto_start_enabled()
            ),
            pystray.MenuItem("自訂專有名詞與設定 (Config)", self.open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("結束程式 (Exit)", self.exit_app)
        )

        hotkey_name = self.config.get('hotkey', 'right ctrl').upper()
        mode_label = self.config.get('typing_mode', 'typeless')
        current_icon = self.idle_icon if self.is_model_ready else self.loading_icon
        current_title = (
            f"FunASRVoiceTyper Turbo (SenseVoice+0.5B | {mode_label} | 熱鍵: {hotkey_name})"
            if self.is_model_ready
            else "FunASRVoiceTyper Turbo (模型載入預熱中...)"
        )
        self.tray_icon = pystray.Icon(
            "FunASRVoiceTyper_Turbo",
            current_icon,
            current_title,
            menu=menu
        )

        print(f"[App] FunASRVoiceTyper Turbo v3.3 啟動成功！常駐熱鍵: {hotkey_name}")
        self.tray_icon.run()


if __name__ == "__main__":
    if not acquire_single_instance_lock():
        print("[App] 偵測到 FunASRVoiceTyper_Turbo 已經在背景執行中，本次啟動自動略過以避免重複載入。")
        sys.exit(0)
    app = HybridVoiceTyperApp()
    app.run()
```

---

## 八、 修改 `build_package.py`（移除冗餘模型與套件封裝，並自動生成純 ASCII + CRLF 啟動批次檔）

請將 `C:\Users\Chery\.gemini\antigravity\scratch\FunASRVoiceTyper_Turbo\build_package.py` 完整覆寫為：

```python
"""
FunASRVoiceTyper_Turbo v3.3 (Lean Golden Edition) 企業綠色免安裝版打包建置腳本
- 僅封裝黃金組合所需之 3 個輕量模型：
  1. models/sensevoice-small-onnx
  2. models/punc_ct-transformer_zh-cn-common-vocab272727-onnx
  3. models/llm (僅含 qwen2.5-0.5b-instruct-q4_k_m.gguf)
- 排除 faster_whisper、ctranslate2、tokenizers 等多餘套件，大幅縮減發布包體積
- 自動生成符合 100% 純 ASCII + CRLF (\r\n) 規範之啟動批次檔
"""

import os
import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import PyInstaller.__main__

base_dir = os.path.dirname(os.path.abspath(__file__))
llm_dir = os.path.abspath(os.path.join(base_dir, "models", "llm"))
sensevoice_dir = os.path.abspath(os.path.join(base_dir, "models", "sensevoice-small-onnx"))
punc_dir = os.path.abspath(os.path.join(base_dir, "models", "punc_ct-transformer_zh-cn-common-vocab272727-onnx"))
config_file = os.path.join(base_dir, "config.json")

for old_dir in [
    os.path.join(base_dir, "build"),
    os.path.join(base_dir, "dist", "FunASRVoiceTyper_Turbo")
]:
    if os.path.exists(old_dir):
        subprocess.run(["cmd.exe", "/c", "rd", "/s", "/q", old_dir], check=False)

print("=================================================================")
print("  開始打包 FunASRVoiceTyper_Turbo v3.3 (極致輕量化黃金組合版)")
print("=================================================================")

args = [
    os.path.join(base_dir, "main.py"),
    "--noconsole",
    "--onedir",
    f"--distpath={os.path.join(base_dir, 'dist')}",
    f"--workpath={os.path.join(base_dir, 'build')}",
    f"--specpath={base_dir}",
    f"--add-data={config_file};.",
]

for src_dir, target_rel in [
    (llm_dir, "models/llm"),
    (sensevoice_dir, "models/sensevoice-small-onnx"),
    (punc_dir, "models/punc_ct-transformer_zh-cn-common-vocab272727-onnx"),
]:
    if os.path.exists(src_dir):
        print(f"納入輕量模型目錄: {src_dir} -> {target_rel}")
        args.append(f"--add-data={src_dir};{target_rel}")

args.extend([
    "--collect-all=llama_cpp",
    "--collect-all=opencc",
    "--collect-all=pystray",
    "--collect-all=sounddevice",
    "--collect-all=funasr_onnx",
    "--collect-all=onnxruntime",
    "--collect-all=jieba",
    "--collect-all=pypinyin",
    "--collect-all=scipy",
    "--exclude-module=faster_whisper",
    "--exclude-module=ctranslate2",
    "--exclude-module=tokenizers",
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    "--exclude-module=torchaudio",
    "--exclude-module=matplotlib",
    "--exclude-module=pytest",
    "--exclude-module=unittest",
    "--exclude-module=IPython",
    "--name=FunASRVoiceTyper_Turbo",
    "--clean",
    "-y"
])

PyInstaller.__main__.run(args)

# 確保 dist 目錄與根目錄之 .bat 啟動檔符合 100% 純 ASCII 與 CRLF (\r\n) 規範
bat_lines = [
    "@echo off",
    "setlocal",
    "cd /d \"%~dp0\"",
    "echo Starting FunASRVoiceTyper_Turbo v3.3 (Lean Golden Edition)...",
    "if exist \"FunASRVoiceTyper_Turbo.exe\" (",
    "    start \"\" \"FunASRVoiceTyper_Turbo.exe\"",
    "    exit /b 0",
    ")",
    "if exist \"dist\\FunASRVoiceTyper_Turbo\\FunASRVoiceTyper_Turbo.exe\" (",
    "    cd /d \"%~dp0dist\\FunASRVoiceTyper_Turbo\"",
    "    start \"\" \"FunASRVoiceTyper_Turbo.exe\"",
    "    exit /b 0",
    ")",
    "if exist \".venv\\Scripts\\pythonw.exe\" (",
    "    start \"\" \".venv\\Scripts\\pythonw.exe\" main.py",
    "    exit /b 0",
    ")",
    "echo [ERROR] Executable or virtual environment not found.",
    "pause",
    ""
]
bat_bytes = "\r\n".join(bat_lines).encode("ascii")

for bat_target in [
    os.path.join(base_dir, "啟動語音輸入_極速版.bat"),
    os.path.join(base_dir, "dist", "FunASRVoiceTyper_Turbo", "啟動語音輸入_極速版.bat"),
    os.path.join(base_dir, "dist", "FunASRVoiceTyper_Turbo", "Start_VoiceTyper.bat"),
]:
    os.makedirs(os.path.dirname(bat_target), exist_ok=True)
    with open(bat_target, "wb") as bf:
        bf.write(bat_bytes)

print("\n=================================================================")
print("  打包完成！產出位於 dist/FunASRVoiceTyper_Turbo 資料夾")
print("=================================================================")
```
