# ============================================================
# 模块：piper-tts 文字转语音（轻量级英文TTS）
# 环境：D:\_BiShe\piper-tts\env
# 依赖：pip install piper-tts
# 模型文件：en_US-amy-medium.onnx + en_US-amy-medium.onnx.json
# 模型下载命令：
#   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" -OutFile "en_US-amy-medium.onnx"
#   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" -OutFile "en_US-amy-medium.onnx.json"
# 注意：piper-tts 使用 CPU 推理，不需要 GPU
# ============================================================

from piper.voice import PiperVoice
import io
import wave

# 加载语音模型（模型文件需放在同目录下）
voice = PiperVoice.load("en_US-amy-medium.onnx")

# 使用内存缓冲区生成音频
buf = io.BytesIO()
with wave.open(buf, "wb") as wav_file:
    # 设置 WAV 参数：单声道、16位、采样率从模型配置读取
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(voice.config.sample_rate)
    # 合成语音（替换为你需要的文本）
    voice.synthesize_wav("Hello, this is a test of the Piper text to speech system.", wav_file)

# 打印生成的字节数（确认音频非空）
print(f"生成字节数: {buf.tell()}")

# 写出到文件
with open("output.wav", "wb") as f:
    f.write(buf.getvalue())

print("完成，已生成 output.wav")
