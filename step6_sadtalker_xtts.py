"""
步骤6: SadTalker + XTTS音频 生成视频
"""
import subprocess
import shutil
from pathlib import Path

# 路径设置
SADTALKER_DIR = Path(r"D:\_BiShe\sadtalker")
SADTALKER_PY = SADTALKER_DIR / "env" / "Scripts" / "python.exe"
IMAGE_FILE = r"D:\_BiShe\demo_1\test_resourse\picture_test.jpg"
AUDIO_FILE = r"D:\_BiShe\demo_1\output\scenario2_xtts_audio_2026.10.30_13.00.30.wav"
OUTPUT_DIR = Path(r"D:\_BiShe\demo_1\output\sadtalker_temp2")
OUTPUT_FILE = r"D:\_BiShe\demo_1\output\scenario2_sadtalker_2026.10.30_13.00.30.mp4"

OUTPUT_DIR.mkdir(exist_ok=True)

print(f"图像: {IMAGE_FILE}")
print(f"音频: {AUDIO_FILE}")
print(f"输出目录: {OUTPUT_DIR}")
print("开始生成视频...")

cmd = [
    str(SADTALKER_PY),
    str(SADTALKER_DIR / "inference.py"),
    "--driven_audio", AUDIO_FILE,
    "--source_image", IMAGE_FILE,
    "--result_dir", str(OUTPUT_DIR),
    "--still",
    "--preprocess", "crop"
]

result = subprocess.run(cmd, cwd=str(SADTALKER_DIR), capture_output=True, text=True)

print(f"返回码: {result.returncode}")
if result.returncode != 0:
    print(f"错误: {result.stderr[:1000]}")
else:
    mp4_files = list(OUTPUT_DIR.glob("*.mp4"))
    if mp4_files:
        latest_mp4 = max(mp4_files, key=lambda p: p.stat().st_mtime)
        print(f"生成视频: {latest_mp4}")
        shutil.move(str(latest_mp4), OUTPUT_FILE)
        print(f"视频已保存: {OUTPUT_FILE}")
        if Path(OUTPUT_FILE).exists():
            print(f"文件大小: {Path(OUTPUT_FILE).stat().st_size} bytes")
