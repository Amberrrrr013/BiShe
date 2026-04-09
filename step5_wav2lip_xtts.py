"""
步骤5: Wav2Lip + XTTS音频 生成视频
"""
import subprocess
from pathlib import Path

# 路径设置
WAV2LIP_DIR = Path(r"D:\_BiShe\wav2lip")
WAV2LIP_PY = WAV2LIP_DIR / "env" / "Scripts" / "python.exe"
CHECKPOINT = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"
IMAGE_FILE = r"D:\_BiShe\demo_1\test_resourse\picture_test.jpg"
AUDIO_FILE = r"D:\_BiShe\demo_1\output\scenario2_xtts_audio_2026.10.30_13.00.30.wav"
OUTPUT_FILE = r"D:\_BiShe\demo_1\output\scenario2_wav2lip_2026.10.30_13.00.30.mp4"

print(f"图像: {IMAGE_FILE}")
print(f"音频: {AUDIO_FILE}")
print(f"输出: {OUTPUT_FILE}")
print("开始生成视频...")

cmd = [
    str(WAV2LIP_PY),
    str(WAV2LIP_DIR / "inference.py"),
    "--checkpoint_path", str(CHECKPOINT),
    "--face", IMAGE_FILE,
    "--audio", AUDIO_FILE,
    "--outfile", OUTPUT_FILE
]

result = subprocess.run(cmd, cwd=str(WAV2LIP_DIR), capture_output=True, text=True)

print(f"返回码: {result.returncode}")
if result.returncode != 0:
    print(f"错误: {result.stderr[:1000]}")
else:
    print(f"视频已保存: {OUTPUT_FILE}")
    if Path(OUTPUT_FILE).exists():
        print(f"文件大小: {Path(OUTPUT_FILE).stat().st_size} bytes")
