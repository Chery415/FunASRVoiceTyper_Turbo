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
