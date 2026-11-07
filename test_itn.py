import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.itn_normalizer import normalize_itn
from core.domain_normalizer import normalize_domain_terms

TERMS = ["程式", "資安", "城市=>程式", "治安=>資安", "API", "AI"]

def post(s):
    return normalize_domain_terms(normalize_itn(normalize_domain_terms(s, TERMS)), TERMS)

CASES = [
    # (輸入, 期望)
    ("我們來測試一下國字一二三和數字一二三", "我們來測試一下國字一二三和數字123"),
    ("我們來測試一下國字123 and數字123", "我們來測試一下國字一二三 and數字123"),
    ("例如 f 1 f 2 f 3", "例如 F1 F2 F3"),
    ("做相關的結構化的1 個行為", "做相關的結構化的一個行為"),
    ("另外1 個版本是什麼", "另外一個版本是什麼"),
    ("這一個版本看一下", "這一個版本看一下"),
    ("我的電話是零九一二三四五六七八", "我的電話是0912345678"),
    ("型號是iPhone十五", "型號是iPhone 15"),
    ("總共五百塊", "總共500塊"),
    ("一共買了十二個", "一共買了12個"),
    ("我買了三個蘋果", "我買了三個蘋果"),
    ("第十二屆大會", "第12屆大會"),
    ("第三點很重要", "第三點很重要"),
    ("成長了百分之三點五", "成長了3.5%"),
    ("下午三點半開會", "下午3:30開會"),
    ("二零二六年五月二十號", "2026年5月20號"),
    ("一石二鳥", "一石二鳥"),
    ("一般來說萬一是這樣", "一般來說萬一是這樣"),
    ("三四個人", "三四個人"),
    ("這種程度還好", "這種程度還好"),
    ("三加五等於八", "3 + 5 = 8"),
    ("這個方案很好", "這個方案很好"),
    ("然後然後我我我覺得", "然後我覺得"),
    ("這個城市有治安問題", "這個程式有資安問題"),
    ("他的反應很快", "他的反應很快"),
]

ok = 0
for inp, exp in CASES:
    out = post(inp)
    flag = "PASS" if out == exp else "FAIL"
    ok += flag == "PASS"
    print(f"[{flag}] {inp}  ->  {out}" + ("" if flag == "PASS" else f"   (期望: {exp})"))
print(f"\n{ok}/{len(CASES)} passed")
