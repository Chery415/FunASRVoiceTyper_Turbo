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
