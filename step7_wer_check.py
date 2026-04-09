"""
步骤7: 用faster-whisper获取时间戳并生成字幕
"""
import subprocess
import json
from pathlib import Path

# 路径设置
FASTER_WHISPER_DIR = Path(r"D:\_BiShe\faster-whisper")
FASTER_WHISPER_PY = FASTER_WHISPER_DIR / "env" / "Scripts" / "python.exe"
AUDIO_FILE = r"D:\_BiShe\demo_1\output\scenario1_piper_audio_2026.10.30_13.00.30.wav"
OUTPUT_DIR = Path(r"D:\_BiShe\demo_1\output")
TIMESTAMP_FILE = OUTPUT_DIR / "words_timestamp.json"
SRT_FILE = OUTPUT_DIR / "subtitles_2026.10.30_13.00.30.srt"

print("开始转录音频...")

whisper_code = '''
from faster_whisper import WhisperModel
import json

model = WhisperModel("medium.en", device="cuda", compute_type="float16")
segments, info = model.transcribe(r"D:\_BiShe\\demo_1\\output\\scenario1_piper_audio_2026.10.30_13.00.30.wav", word_timestamps=True)

print(f"语言: {info.language}, 置信度: {info.language_probability:.2f}")

words_data = []
for segment in segments:
    for word in segment.words:
        words_data.append({
            "word": word.word.strip(),
            "start": word.start,
            "end": word.end
        })
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

# 保存时间戳
with open(r"D:\_BiShe\\demo_1\\output\\words_timestamp.json", "w", encoding="utf-8") as f:
    json.dump(words_data, f, ensure_ascii=False)

print(f"保存了 {len(words_data)} 个词的时间戳")
'''

result = subprocess.run(
    [str(FASTER_WHISPER_PY), "-c", whisper_code],
    capture_output=True,
    text=True,
    cwd=str(FASTER_WHISPER_DIR),
    timeout=180
)

print(f"返回码: {result.returncode}")
if result.returncode != 0:
    print(f"错误: {result.stderr[:500]}")
else:
    print(f"输出: {result.stdout[:500]}")
    
    # 读取时间戳并生成SRT
    if TIMESTAMP_FILE.exists():
        with open(TIMESTAMP_FILE, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        print(f"获取到 {len(words_data)} 个词的时间戳")
        
        # 生成SRT字幕
        def format_srt_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        lines = []
        words_per_line = 8
        current_line = []
        current_start = None
        current_end = None
        
        for word_info in words_data:
            word = word_info["word"]
            start = word_info["start"]
            end = word_info["end"]
            
            current_line.append(word)
            if current_start is None:
                current_start = start
            current_end = end
            
            if len(current_line) >= words_per_line:
                lines.append({
                    "text": " ".join(current_line),
                    "start": current_start,
                    "end": current_end
                })
                current_line = []
                current_start = None
        
        if current_line:
            lines.append({
                "text": " ".join(current_line),
                "start": current_start,
                "end": current_end
            })
        
        # 写入SRT
        with open(SRT_FILE, 'w', encoding='utf-8') as f:
            for i, line in enumerate(lines, 1):
                f.write(f"{i}\n")
                f.write(f"{format_srt_time(line['start'])} --> {format_srt_time(line['end'])}\n")
                f.write(f"{line['text']}\n\n")
        
        print(f"字幕文件已生成: {SRT_FILE}")
