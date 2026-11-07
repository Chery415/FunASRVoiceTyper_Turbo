import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
from core.asr_engine import Stage1ASREngine

eng = Stage1ASREngine(default_engine="sensevoice")
print("SenseVoice loaded:", eng.sensevoice_model is not None)
print("Punc model loaded:", eng.punc is not None)
if eng.punc:
    r = eng.punc("好我們來測試一下這個新的版本看一下它是不是真的已經修復了這個錯誤")
    print("Punc sample:", r[0])
print("Switch to Paraformer ->", eng.switch_engine("Paraformer-large"))
print("Paraformer loaded:", eng.paraformer_model is not None)
