"""
配置模块示例 - 复制此文件为 config.py 并填写你的 API key
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# 模型路径配置 - 指向父目录的各个模型
PARENT_DIR = Path(r"D:\_BiShe")

# TTS模型路径
PIPER_MODEL_PATH = PARENT_DIR / "piper-tts" / "en_US-amy-medium.onnx"
XTTS_MODEL_PATH = PARENT_DIR / "xtts-v2"

# Whisper模型路径 (用于WER检测)
WHISPER_MODEL_PATH = PARENT_DIR / "faster-whisper"

# 视频生成模型路径
WAV2LIP_MODEL_PATH = PARENT_DIR / "wav2lip"
SADTALKER_MODEL_PATH = PARENT_DIR / "sadtalker"

# 图像处理模型路径
GFPGAN_MODEL_PATH = PARENT_DIR / "gfpgan"

# 各模型虚拟环境的 Python 解释器路径
WAV2LIP_PY = WAV2LIP_MODEL_PATH / "env" / "Scripts" / "python.exe"
SADTALKER_PY = SADTALKER_MODEL_PATH / "env" / "Scripts" / "python.exe"
GFPGAN_PY = GFPGAN_MODEL_PATH / "env" / "Scripts" / "python.exe"
FASTER_WHISPER_PY = WHISPER_MODEL_PATH / "env" / "Scripts" / "python.exe"
PIPER_TTS_PY = PIPER_MODEL_PATH.parent / "env" / "Scripts" / "python.exe"
XTTS_PY = XTTS_MODEL_PATH / "env" / "Scripts" / "python.exe"

# 创建必要的输出目录
for subdir in ["text", "audio", "image", "video", "final"]:
    (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)

# WER阈值配置
WER_THRESHOLD = 0.15
MAX_TTS_RETRIES = 5

# API配置 - 从环境变量读取，不要硬编码！
def _get_env(key, default="", desc=""):
    """安全获取环境变量"""
    value = os.environ.get(key, default)
    if not value and default == "":
        print(f"[警告] 环境变量 {key} 未设置！{desc}")
    return value

# MiniMax API Key - 请设置环境变量 MINIMAX_API_KEY
MINIMAX_API_KEY = _get_env(
    "MINIMAX_API_KEY",
    desc="MiniMax API密钥，用于文本生成、TTS和图片生成"
)

API_CONFIG = {
    "text_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "MiniMax-Text-01",
        "base_url": "https://api.minimaxi.com/v1"
    },
    "tts_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "speech-2.8-hd",
        "voice_id": "English_Graceful_Lady",
        "voice_options": [
            {"id": "English_Graceful_Lady", "name": "优雅女士 (English Graceful Lady)"},
            {"id": "Sweet_Girl", "name": "甜美女孩 (Sweet Girl)"},
            {"id": "English_Trustworthy_Man", "name": "可靠男士 (English Trustworthy Man)"}
        ],
        "base_url": "https://api.minimaxi.com",
        "voice": "en-US-JennyNeural"
    },
    "image_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "image-01",
        "base_url": "https://api.minimaxi.com",
        "aspect_ratio": "1:1",
        "style_type": "",
        "aigc_watermark": False
    },
    "video_api": {
        "provider": "local",
        "api_key": ""
    }
}
