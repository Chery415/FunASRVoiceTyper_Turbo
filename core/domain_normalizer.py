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
