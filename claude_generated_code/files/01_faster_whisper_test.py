# ============================================================
# 模块：faster-whisper 语音转文字
# 环境：D:\_BiShe\faster-whisper\env
# 依赖：pip install faster-whisper nvidia-cudnn-cu12
# 模型：medium.en（首次运行自动下载，约1.5GB）
# 模型缓存位置：C:\Users\ASUS\.cache\huggingface\hub\
# ============================================================

from faster_whisper import WhisperModel

# 加载模型
# device="cuda" 使用 GPU 加速
# compute_type="float16" 半精度推理，节省显存
model = WhisperModel("medium.en", device="cuda", compute_type="float16")

# 转录音频文件（替换为你自己的音频路径）
segments, info = model.transcribe(r"D:\_BiShe\whisper_test\test_1.wav")

# 输出检测到的语言和置信度
print(f"检测语言: {info.language}, 置信度: {info.language_probability:.2f}")

# 逐段输出转录结果，带时间戳
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
