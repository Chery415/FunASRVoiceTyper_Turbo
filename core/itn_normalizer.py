"""
SPEECH-PIPELINE-HYBRID-FAST: 本地逆文本正規化 (ITN - Inverse Text Normalization) v2.1

設計原則（依台灣書寫習慣，保守轉換）：
- 「該用數字的地方用數字」：金額、度量衡、百分比、年份日期時間、電話/序號、型號、十以上的數量。
- 「該留國字的地方留國字」：十以內的一般量詞（一個、三次、這一個版本）、成語慣用語、概數（三四個、七八十）。
- 語音指令「國字一二三」/「中文數字一二三」→ 強制保留國字。
- 單一英文字母 + 數字合併：「f 1 f 2」→「F1 F2」。
"""

import re
from typing import Optional

CN_NUM_MAP = {
    '零': 0, '〇': 0, '一': 1, '壹': 1, '二': 2, '貳': 2, '兩': 2, '俩': 2,
    '三': 3, '參': 3, '叁': 3, '四': 4, '肆': 4, '五': 5, '伍': 5,
    '六': 6, '陸': 6, '七': 7, '柒': 7, '八': 8, '捌': 8, '九': 9, '玖': 9,
}
CN_UNIT_MAP = {
    '十': 10, '拾': 10, '百': 100, '佰': 100, '千': 1000, '仟': 1000,
    '萬': 10000, '万': 10000, '億': 100000000, '亿': 100000000,
}
DIGIT_TO_CN = {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
               '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}

# 成語、慣用語與概數白名單（一律保留國字）
IDIOM_WHITELIST = [
    "一般", "一半", "一點點", "一下子", "一下", "一會兒", "一起", "一直", "一定", "一樣",
    "一切", "一些", "一致", "一旦", "一向", "一共", "一律", "一方面", "一邊", "一路",
    "統一", "唯一", "萬一", "第一時間", "一石二鳥", "萬無一失", "一五一十", "一模一樣",
    "一心一意", "獨一無二", "一乾二淨", "三心二意", "三三兩兩", "朝三暮四", "五顏六色",
    "七上八下", "亂七八糟", "七七八八", "九牛一毛", "十全十美", "十之八九", "百發百中",
    "千方百計", "萬紫千紅", "千萬", "一一", "不二", "二話不說", "說一不二", "四面八方",
    "三番兩次", "接二連三", "一舉兩得", "兩全其美", "一清二楚", "九九乘法",
]

# 一般量詞（十以內保留國字，十以上才轉數字）
GENERAL_MEASURE = r'(?:個|次|位|件|種|項|句|段|篇|份|批|組|輪|遍|下|些|點兒|名|條|隻|本|張|台|部|支|顆|套|場|間|家|群|層|步|招|頁|行)'
# 度量/金額/時間單位（任何數值都轉數字）
STRICT_UNIT = r'(?:元|塊錢|塊|角|美元|美金|台幣|日圓|歐元|萬元|億元|公尺|公分|公里|公釐|毫米|釐米|公克|公斤|克|噸|毫升|公升|坪|平方公尺|GB|MB|TB|KB|G|M|K|歲|週年|樓|號|室|秒|分鐘|小時|毫秒|倍|折|成)'

CN_DIGITS = r'[零〇一二兩三四五六七八九]'
CN_NUM = r'[零〇一壹二貳兩三參四肆五伍六陸七柒八捌九玖十拾百佰千仟萬万億亿]'


def chinese_to_number(cn_str: str) -> Optional[int]:
    """將中文數字（八十、一百二十、兩千五百、二零二六）轉為整數；無法解析時回傳 None"""
    if not cn_str:
        return None
    if all(ch in CN_NUM_MAP for ch in cn_str):
        if len(cn_str) == 1:
            return CN_NUM_MAP[cn_str]
        return int("".join(str(CN_NUM_MAP[c]) for c in cn_str))

    total, section, number = 0, 0, 0
    for ch in cn_str:
        if ch in CN_NUM_MAP:
            number = CN_NUM_MAP[ch]
        elif ch in CN_UNIT_MAP:
            unit = CN_UNIT_MAP[ch]
            if unit >= 10000:
                section = (section + number) * unit
                total += section
                section, number = 0, 0
            else:
                if number == 0 and unit == 10:
                    number = 1  # 「十二」省略開頭的一
                section += number * unit
                number = 0
        else:
            return None
    return total + section + number


def _cn_or_digit_to_str(s: str) -> str:
    if '點' in s:
        a, b = s.split('點', 1)
        ia = chinese_to_number(a) if a else 0
        if ia is None:
            return s
        return f"{ia}." + "".join(str(CN_NUM_MAP.get(c, c)) for c in b)
    v = chinese_to_number(s)
    return str(v) if v is not None else s


class ITNNormalizer:
    def normalize(self, text: str) -> str:
        if not text:
            return ""

        # --- 0. 保護白名單與「國字」語音指令 ---
        protected = {}

        def _protect(s: str) -> str:
            key = f"\uE000{len(protected)}\uE001"
            protected[key] = s
            return key

        # 「國字一二三」「中文的數字三」→ 強制保留國字（若 ASR 已輸出阿拉伯數字，轉回國字）
        def _keep_cn(m):
            prefix, num = m.group(1), m.group(2)
            num_cn = "".join(DIGIT_TO_CN.get(c, c) for c in num)
            return prefix + _protect(num_cn)
        text = re.sub(r'(國字|中文|中文數字|大寫數字)(?:的)?(?:數字)?\s*([0-9零〇一二兩三四五六七八九十百千萬]+)', _keep_cn, text)

        for idiom in sorted(IDIOM_WHITELIST, key=len, reverse=True):
            if idiom in text:
                text = text.replace(idiom, _protect(idiom))

        res = text

        # --- 1. 百分比 ---
        res = re.sub(r'百分之\s*(' + CN_NUM + r'+(?:點' + CN_NUM + r'+)?|\d+(?:\.\d+)?)',
                     lambda m: _cn_or_digit_to_str(m.group(1)) + '%', res)
        res = re.sub(r'(' + CN_NUM + r'+(?:點' + CN_NUM + r'+)?|\d+(?:\.\d+)?)\s*(?:percent|Percent|PERCENT|％)',
                     lambda m: _cn_or_digit_to_str(m.group(1)) + '%', res)

        # --- 2. 溫度（需有「攝氏」或「度C」明確標記，避免「這一度」「程度」誤轉） ---
        res = re.sub(r'攝氏\s*(' + CN_NUM + r'+(?:點' + CN_NUM + r'+)?|\d+(?:\.\d+)?)\s*度',
                     lambda m: _cn_or_digit_to_str(m.group(1)) + '°C', res)
        res = re.sub(r'(' + CN_NUM + r'+(?:點' + CN_NUM + r'+)?|\d+(?:\.\d+)?)\s*度\s*[cC]',
                     lambda m: _cn_or_digit_to_str(m.group(1)) + '°C', res)

        # --- 3. 年份與日期 ---
        res = re.sub(r'(' + CN_DIGITS + r'{4})\s*年',
                     lambda m: "".join(str(CN_NUM_MAP[c]) for c in m.group(1)) + '年', res)
        res = re.sub(r'(' + CN_NUM + r'{1,3})\s*月\s*(' + CN_NUM + r'{1,3})\s*(號|日)',
                     lambda m: f"{chinese_to_number(m.group(1))}月{chinese_to_number(m.group(2))}{m.group(3)}"
                     if chinese_to_number(m.group(1)) and chinese_to_number(m.group(2)) else m.group(0), res)

        # --- 4. 時間：三點半、十點十五分、下午兩點 ---
        def _time(m):
            h = chinese_to_number(m.group(1))
            if h is None or h > 24:
                return m.group(0)
            tail = m.group(2) or ""
            if tail == "半":
                return f"{h}:30"
            if tail:
                mi = chinese_to_number(tail.rstrip("分"))
                if mi is not None and mi < 60:
                    return f"{h}:{mi:02d}"
            return m.group(0)
        res = re.sub(r'(?<=[上下中晚早凌午點鐘約到至前後])\s*(' + CN_NUM + r'{1,3})點(半|' + CN_NUM + r'{1,3}分)', _time, res)
        res = re.sub(r'^(' + CN_NUM + r'{1,3})點(半|' + CN_NUM + r'{1,3}分)', _time, res)

        # --- 5. 小數：三點五（排除時間已處理者） ---
        res = re.sub(r'(' + CN_NUM + r'+)點(' + CN_DIGITS + r'+)(?!分)',
                     lambda m: _cn_or_digit_to_str(m.group(1) + '點' + m.group(2)), res)

        # --- 6. 電話/序號/房號：連續 3 碼以上的純數字讀法（零九一二、一二三） ---
        res = re.sub(r'(' + CN_DIGITS + r'{3,})',
                     lambda m: "".join(str(CN_NUM_MAP[c]) for c in m.group(1)), res)

        # --- 7. 英文型號 + 中文數字：iPhone 十五、RTX 四零九零 ---
        res = re.sub(r'([A-Za-z]{2,})\s*(' + CN_NUM + r'+)(?![個次位件種項])',
                     lambda m: f"{m.group(1)} {chinese_to_number(m.group(2))}"
                     if chinese_to_number(m.group(2)) is not None else m.group(0), res)

        # --- 8. 金額與度量衡：任何數值都轉阿拉伯數字（概數「三四塊」除外） ---
        def _is_approx(s: str) -> bool:
            return len(s) == 2 and all(c in CN_NUM_MAP for c in s) and s[0] != s[1]

        res = re.sub(r'(' + CN_NUM + r'+)\s*(' + STRICT_UNIT + r')',
                     lambda m: f"{chinese_to_number(m.group(1))}{m.group(2)}"
                     if chinese_to_number(m.group(1)) is not None and not _is_approx(m.group(1)) else m.group(0), res)

        # --- 9. 一般量詞：十以上才轉數字（十以內與概數保留國字，如「一個」「三次」「三四個」） ---
        def _measure(m):
            v = chinese_to_number(m.group(1))
            if v is None or v < 10 or _is_approx(m.group(1)):
                return m.group(0)
            return f"{v}{m.group(2)}"
        res = re.sub(r'(' + CN_NUM + r'+)\s*(' + GENERAL_MEASURE + r')', _measure, res)

        # --- 10. 序數：第十二屆 → 第12屆（十以內保留，如「第三」） ---
        def _ordinal(m):
            v = chinese_to_number(m.group(1))
            if v is None or v < 10:
                return m.group(0)
            return f"第{v}"
        res = re.sub(r'第(' + CN_NUM + r'+)', _ordinal, res)

        # --- 11. ASR 內建 ITN 過度轉換回復：「這1個」「1次」→「這一個」「一次」 ---
        res = re.sub(r'(?<![\d.\-:/A-Za-z])([1-9])\s?(' + GENERAL_MEASURE + r')',
                     lambda m: DIGIT_TO_CN[m.group(1)] + m.group(2), res)

        # --- 12. 單一字母 + 數字合併（支援中文數字）：f 1 → F1、F 一 → F1、p 2 → P2 ---
        def _composite(m):
            letter = m.group(1).upper()
            num_str = m.group(2)
            if num_str in CN_NUM_MAP:
                num_str = str(CN_NUM_MAP[num_str])
            return letter + num_str
        res = re.sub(r'(?<![A-Za-z])([A-Za-z])\s*(\d{1,2}|[零〇一二兩三四五六七八九十])(?!\d)', _composite, res)

        # --- 13. 數學運算式（僅在完整「A 加 B 等於 C」結構時轉換，避免誤傷「增加」「等於是」） ---
        num_tok = r'(\d+(?:\.\d+)?|' + CN_NUM + r'+(?:點' + CN_DIGITS + r'+)?)'
        ops = {'加': '+', '減': '-', '乘以': '×', '乘': '×', '除以': '÷'}
        res = re.sub(num_tok + r'\s*(加|減|乘以|乘|除以)\s*' + num_tok + r'\s*等於\s*' + num_tok,
                     lambda m: f"{_cn_or_digit_to_str(m.group(1))} {ops[m.group(2)]} "
                               f"{_cn_or_digit_to_str(m.group(3))} = {_cn_or_digit_to_str(m.group(4))}", res)

        # --- 還原保護字串 ---
        for key, val in protected.items():
            res = res.replace(key, val)
        return res


_default_normalizer = ITNNormalizer()


def normalize_itn(text: str) -> str:
    """快速執行逆文本正規化 (ITN) 轉換"""
    return _default_normalizer.normalize(text)
