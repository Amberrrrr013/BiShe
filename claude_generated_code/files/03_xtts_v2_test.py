# ============================================================
# 模块：XTTS-v2 高质量音色克隆 TTS
# 环境：D:\_BiShe\xtts-v2\env
# 依赖：
#   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
#   pip install TTS
#   pip install transformers==4.40.0
# 模型：首次运行自动下载（约1.8GB）
# 模型缓存位置：C:\Users\ASUS\AppData\Local\tts\
# 
# 注意事项：
#   - 首次运行会提示同意 CPML 许可证，输入 y 确认
#   - XTTS-v2 为非商业授权（CPML），商业用途需购买许可
#   - speaker_wav 为音色参考音频，6秒以上效果更好
#   - 支持语言：en, zh-cn, fr, de, es 等17种语言
# ============================================================

from TTS.api import TTS

# 加载 XTTS-v2 模型，使用 GPU 推理
# 警告 "`gpu` will be deprecated" 可忽略，不影响功能
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

# 生成语音
# text: 要合成的文本
# speaker_wav: 用于克隆音色的参考音频（替换为你自己的音频路径）
# language: 语言代码
# file_path: 输出文件路径
tts.tts_to_file(
    text="Hello, this is a test of XTTS version 2. The voice cloning is working correctly.",
    speaker_wav="D:\\_BiShe\\whisper_test\\test_1.wav",
    language="en",
    file_path="output.wav"
)

print("完成，已生成 output.wav")
