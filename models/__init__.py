"""
demo_1 - AI 英语演讲视频自动生成系统
基于 LangGraph 的模块化工作流系统

模块:
- text: 文本生成/读取模块
- tts: 文本转语音模块(含WER检测)
- image: 图像处理模块
- video: 视频生成模块
"""

from .text import TextManager, SpeechRequest, TextProvider
from .tts import TTSManager, TTSResult, WERDetector
from .image import ImageManager, ImageResult, GFPGANEnhancer
from .video import VideoManager, VideoResult

__all__ = [
    # Text
    'TextManager',
    'SpeechRequest', 
    'TextProvider',
    # TTS
    'TTSManager',
    'TTSResult',
    'WERDetector',
    # Image
    'ImageManager',
    'ImageResult',
    'GFPGANEnhancer',
    # Video
    'VideoManager',
    'VideoResult',
]
