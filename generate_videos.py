"""
视频生成执行脚本
基于已测试成功的代码生成演讲视频
"""
import subprocess
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 设置路径 - 使用项目根目录的父目录作为模型根目录
PROJECT_DIR = Path(__file__).parent
MODEL_ROOT = Path(os.getenv("MODEL_ROOT", str(PROJECT_DIR.parent)))

TEST_RESOURCE_DIR = PROJECT_DIR / "test_resourse"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 各模型路径
WAV2LIP_DIR = MODEL_ROOT / "wav2lip"
SADTALKER_DIR = MODEL_ROOT / "sadtalker"
GFPGAN_DIR = MODEL_ROOT / "gfpgan"
FASTER_WHISPER_DIR = MODEL_ROOT / "faster-whisper"
PIPER_TTS_DIR = MODEL_ROOT / "piper-tts"
XTTS_DIR = MODEL_ROOT / "xtts-v2"

# Python解释器路径
WAV2LIP_PY = WAV2LIP_DIR / "env" / "Scripts" / "python.exe"
SADTALKER_PY = SADTALKER_DIR / "env" / "Scripts" / "python.exe"
GFPGAN_PY = GFPGAN_DIR / "env" / "Scripts" / "python.exe"
FASTER_WHISPER_PY = FASTER_WHISPER_DIR / "env" / "Scripts" / "python.exe"
PIPER_TTS_PY = PIPER_TTS_DIR / "env" / "Scripts" / "python.exe"
XTTS_PY = XTTS_DIR / "env" / "Scripts" / "python.exe"

# 测试资源
TEXT_FILE = TEST_RESOURCE_DIR / "text_test.txt"
AUDIO_FILE = TEST_RESOURCE_DIR / "speech_test.wav"
IMAGE_FILE = TEST_RESOURCE_DIR / "picture_test.jpg"

# 读取文本内容
def read_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# 创建时间戳命名前缀
TIMESTAMP = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
print(f"时间戳: {TIMESTAMP}")

def run_command(cmd, cwd=None, timeout=None):
    """执行命令并返回结果"""
    print(f"执行命令: {' '.join(cmd)[:100]}...")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"错误输出: {result.stderr[:500]}")
    return result

# =============================================================================
# 情形1: Piper TTS (无音色克隆) + Wav2Lip
# =============================================================================
print("\n" + "="*60)
print("情形1.1: Piper TTS + Wav2Lip")
print("="*60)

# 1. Piper TTS 生成音频
piper_output = OUTPUT_DIR / f"scenario1_wav2lip_piper_{TIMESTAMP}.wav"
piper_script = PIPER_TTS_DIR / "test.py"

text_content = read_text(TEXT_FILE)
# Piper单次合成有长度限制，我们分段合成
piper_cmd = [
    str(PIPER_TTS_PY), "-c",
    f"from piper.voice import PiperVoice; import io, wave; voice = PiperVoice.load(r'{PIPER_TTS_DIR}/en_US-amy-medium.onnx'); buf = io.BytesIO(); wav_file = wave.open(buf, 'wb'); wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(voice.config.sample_rate); voice.synthesize_wav('''{text_content[:500]}''', wav_file); buf.seek(0); open(r'{piper_output}', 'wb').write(buf.getvalue()); print('Piper完成')"
]
result = run_command(piper_cmd)
print(f"Piper TTS 返回码: {result.returncode}")

# 2. Wav2Lip 生成视频
wav2lip_checkpoint = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"
video1_output = OUTPUT_DIR / f"scenario1_wav2lip_{TIMESTAMP}.mp4"

wav2lip_cmd = [
    str(WAV2LIP_PY),
    str(WAV2LIP_DIR / "inference.py"),
    "--checkpoint_path", str(wav2lip_checkpoint),
    "--face", str(IMAGE_FILE),
    "--audio", str(piper_output),
    "--outfile", str(video1_output)
]
result = run_command(wav2lip_cmd, cwd=str(WAV2LIP_DIR), timeout=600)
print(f"Wav2Lip 返回码: {result.returncode}")

if video1_output.exists():
    print(f"✓ 情形1.1视频生成成功: {video1_output}")
else:
    print(f"✗ 情形1.1视频生成失败")

print("\n" + "="*60)
print("情形1.2: Piper TTS + SadTalker")
print("="*60)

# SadTalker 生成视频
video2_output = OUTPUT_DIR / f"scenario1_sadtalker_{TIMESTAMP}.mp4"

sadtalker_cmd = [
    str(SADTALKER_PY),
    str(SADTALKER_DIR / "inference.py"),
    "--driven_audio", str(piper_output),
    "--source_image", str(IMAGE_FILE),
    "--result_dir", str(OUTPUT_DIR / "temp_sadtalker"),
    "--still",
    "--preprocess", "crop"
]
result = run_command(sadtalker_cmd, cwd=str(SADTALKER_DIR), timeout=1200)

# 移动输出文件
temp_dir = OUTPUT_DIR / "temp_sadtalker"
if temp_dir.exists():
    mp4_files = list(temp_dir.glob("*.mp4"))
    if mp4_files:
        latest_mp4 = max(mp4_files, key=lambda p: p.stat().st_mtime)
        shutil.move(str(latest_mp4), str(video2_output))
        print(f"✓ 情形1.2视频生成成功: {video2_output}")
    else:
        print(f"✗ SadTalker未生成视频文件")
else:
    print(f"✗ SadTalker执行失败")

print("\n" + "="*60)
print("情形2.1: XTTS音色克隆 + Wav2Lip")
print("="*60)

# 1. XTTS V2 生成音频（音色克隆）
xtts_output = OUTPUT_DIR / f"scenario2_wav2lip_xtts_{TIMESTAMP}.wav"
xtts_script = XTTS_DIR / "test.py"

# 使用XTTS的test.py脚本
xtts_cmd = [
    str(XTTS_PY), "-c",
    f"from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True); tts.tts_to_file(text='''{text_content[:500]}''', speaker_wav=r'{AUDIO_FILE}', language='en', file_path=r'{xtts_output}'); print('XTTS完成')"
]
result = run_command(xtts_cmd, timeout=300)
print(f"XTTS 返回码: {result.returncode}")

# 2. Wav2Lip 生成视频
video3_output = OUTPUT_DIR / f"scenario2_wav2lip_{TIMESTAMP}.mp4"

wav2lip_cmd = [
    str(WAV2LIP_PY),
    str(WAV2LIP_DIR / "inference.py"),
    "--checkpoint_path", str(wav2lip_checkpoint),
    "--face", str(IMAGE_FILE),
    "--audio", str(xtts_output),
    "--outfile", str(video3_output)
]
result = run_command(wav2lip_cmd, cwd=str(WAV2LIP_DIR), timeout=600)
print(f"Wav2Lip 返回码: {result.returncode}")

if video3_output.exists():
    print(f"✓ 情形2.1视频生成成功: {video3_output}")
else:
    print(f"✗ 情形2.1视频生成失败")

print("\n" + "="*60)
print("情形2.2: XTTS音色克隆 + SadTalker")
print("="*60)

# SadTalker 生成视频
video4_output = OUTPUT_DIR / f"scenario2_sadtalker_{TIMESTAMP}.mp4"

sadtalker_cmd = [
    str(SADTALKER_PY),
    str(SADTALKER_DIR / "inference.py"),
    "--driven_audio", str(xtts_output),
    "--source_image", str(IMAGE_FILE),
    "--result_dir", str(OUTPUT_DIR / "temp_sadtalker2"),
    "--still",
    "--preprocess", "crop"
]
result = run_command(sadtalker_cmd, cwd=str(SADTALKER_DIR), timeout=1200)

# 移动输出文件
temp_dir2 = OUTPUT_DIR / "temp_sadtalker2"
if temp_dir2.exists():
    mp4_files = list(temp_dir2.glob("*.mp4"))
    if mp4_files:
        latest_mp4 = max(mp4_files, key=lambda p: p.stat().st_mtime)
        shutil.move(str(latest_mp4), str(video4_output))
        print(f"✓ 情形2.2视频生成成功: {video4_output}")
    else:
        print(f"✗ SadTalker未生成视频文件")

print("\n" + "="*60)
print("视频生成完成!")
print("="*60)
print(f"输出目录: {OUTPUT_DIR}")

# 列出所有生成的视频
for f in OUTPUT_DIR.glob("*.mp4"):
    print(f"  - {f.name}")
