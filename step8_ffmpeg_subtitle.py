"""
步骤8: FFmpeg 烧录字幕到视频
"""
import subprocess
from pathlib import Path

# 路径设置
VIDEO_FILE = r"D:\_BiShe\demo_1\output\scenario1_wav2lip_2026.10.30_13.00.30.mp4"
SRT_FILE = r"D:\_BiShe\demo_1\output\subtitles_2026.10.30_13.00.30.srt"
OUTPUT_FILE = r"D:\_BiShe\demo_1\output\scenario1_wav2lip_subtitled_2026.10.30_13.00.30.mp4"

print(f"输入视频: {VIDEO_FILE}")
print(f"字幕文件: {SRT_FILE}")
print(f"输出视频: {OUTPUT_FILE}")

# FFmpeg命令 - 使用字幕滤镜
cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_FILE,
    "-vf", f"subtitles='{SRT_FILE}'",
    "-c:a", "copy",
    OUTPUT_FILE
]

print("开始烧录字幕...")
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"返回码: {result.returncode}")
if result.returncode != 0:
    print(f"错误: {result.stderr[:500]}")
else:
    if Path(OUTPUT_FILE).exists():
        print(f"字幕视频已生成: {OUTPUT_FILE}")
        print(f"文件大小: {Path(OUTPUT_FILE).stat().st_size} bytes")
