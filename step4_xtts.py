"""
步骤4: XTTS V2 音色克隆生成音频
"""
import sys
from pathlib import Path

# 路径设置
XTTS_DIR = Path(r"D:\_BiShe\xtts-v2")
XTTS_PY = XTTS_DIR / "env" / "Scripts" / "python.exe"
TEXT_FILE = r"D:\_BiShe\demo_1\test_resourse\text_test.txt"
REFERENCE_AUDIO = r"D:\_BiShe\demo_1\test_resourse\speech_test.wav"
OUTPUT_FILE = r"D:\_BiShe\demo_1\output\scenario2_xtts_audio_2026.10.30_13.00.30.wav"

# 读取文本
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# 限制文本长度
text = text[:300]

print(f"参考音频: {REFERENCE_AUDIO}")
print(f"文本长度: {len(text)}")
print("开始生成音频...")

# 使用Python代码执行XTTS
xtts_code = f'''
import sys
sys.path.insert(0, r"{XTTS_DIR}")
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.tts_to_file(
    text="""{text}""",
    speaker_wav=r"{REFERENCE_AUDIO}",
    language="en",
    file_path=r"{OUTPUT_FILE}"
)
print("XTTS完成")
'''

# 执行
import subprocess
result = subprocess.run(
    [str(XTTS_PY), "-c", xtts_code],
    capture_output=True,
    text=True,
    timeout=300
)

print(f"返回码: {result.returncode}")
if result.returncode != 0:
    print(f"错误: {result.stderr[:1000]}")
else:
    print(f"音频已保存: {OUTPUT_FILE}")
    if Path(OUTPUT_FILE).exists():
        print(f"文件大小: {Path(OUTPUT_FILE).stat().st_size} bytes")
