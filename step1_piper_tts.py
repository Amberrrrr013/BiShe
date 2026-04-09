"""
步骤1: Piper TTS 生成音频
"""
import sys
import io
import wave
from pathlib import Path

# 添加piper路径
sys.path.insert(0, r"D:\_BiShe\piper-tts")
from piper.voice import PiperVoice

# 路径设置
PIPER_MODEL = r"D:\_BiShe\piper-tts\en_US-amy-medium.onnx"
TEXT_FILE = r"D:\_BiShe\demo_1\test_resourse\text_test.txt"
OUTPUT_FILE = r"D:\_BiShe\demo_1\output\scenario1_piper_audio_2026.10.30_13.00.30.wav"

# 读取文本
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# 清理文本（piper对长文本支持不好，我们取前500字符）
text = text[:500].replace("'", "").replace('"', '')

print(f"文本长度: {len(text)}")
print("开始生成音频...")

# 加载语音模型
voice = PiperVoice.load(PIPER_MODEL)

# 生成音频
buf = io.BytesIO()
with wave.open(buf, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(voice.config.sample_rate)
    voice.synthesize_wav(text, wav_file)

# 写出到文件
with open(OUTPUT_FILE, 'wb') as f:
    f.write(buf.getvalue())

print(f"音频已保存: {OUTPUT_FILE}")
print(f"文件大小: {buf.tell()} bytes")
