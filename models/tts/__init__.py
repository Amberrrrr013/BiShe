"""
文本转语音模块
支持三种模式:
1. Piper TTS - 本地固定模型
2. XTTS V2 - 音色模仿
3. 在线TTS API

包含WER (Word Error Rate) 检测功能
"""

import io
import wave
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import sys

# 添加父目录到路径以便导入config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import (
    XTTS_MODEL_PATH,
    XTTS_PY,
    FASTER_WHISPER_PY,
    PIPER_MODEL_PATH,
    PIPER_TTS_PY,
)

from config import (
    PIPER_MODEL_PATH,
    WHISPER_MODEL_PATH,
    WER_THRESHOLD,
    MAX_TTS_RETRIES,
    API_CONFIG,
    OUTPUT_DIR,
)


@dataclass
class TTSResult:
    """TTS结果数据结构"""

    audio_path: str
    duration: float
    wer_score: float = 0.0
    retries: int = 0
    success: bool = True
    error_msg: str = ""


@dataclass
class WERResult:
    """WER检测结果"""

    wer: float
    wer_percentage: float
    total_words: int
    errors: int
    details: List[Dict[str, Any]]


class TTSProvider(ABC):
    """TTS提供者抽象基类"""

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> Tuple[str, float]:
        """
        合成语音

        Args:
            text: 输入文本
            output_path: 输出音频路径

        Returns:
            Tuple[str, float]: (音频路径, 时长秒数)
        """
        pass


class PiperTTSProvider(TTSProvider):
    """Piper TTS 本地固定模型"""

    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(PIPER_MODEL_PATH)
        self._python_exe = str(PIPER_TTS_PY)

    def synthesize(self, text: str, output_path: str) -> Tuple[str, float]:
        # 使用subprocess调用piper-tts虚拟环境的Python执行TTS
        import subprocess

        piper_base = Path(self.model_path).parent
        piper_site_packages = piper_base / "env" / "Lib" / "site-packages"

        script = f'''
import sys
sys.path.insert(0, r"{piper_site_packages}")
from piper.voice import PiperVoice
import wave

print("Piper进度: 正在加载模型...")
voice = PiperVoice.load(r"{self.model_path}")
sample_rate = voice.config.sample_rate
print("Piper进度: 模型加载完成，正在合成语音...")

with wave.open(r"{output_path}", "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    voice.synthesize_wav({repr(text)}, wav_file)

# 计算时长
with wave.open(r"{output_path}", "rb") as wav_file:
    frames = wav_file.getnframes()
    duration = frames / wav_file.getframerate()
print(f"Piper完成: 生成的音频时长 {{duration:.1f}} 秒")
'''

        try:
            result = subprocess.run(
                [self._python_exe, "-c", script],
                capture_output=True,
                text=True,
                timeout=300,
            )

            # 打印 Piper 的进度输出
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"  [Piper] {line}")

            if result.returncode != 0:
                raise RuntimeError(f"Piper执行失败: {result.stderr[:2000]}")

            # 解析时长
            duration = 0.0
            import re

            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                match = re.search(r"生成的音频时长\s*(\d+\.?\d*)\s*秒", line)
                if match:
                    duration = float(match.group(1))

            if duration == 0.0:
                raise RuntimeError(
                    f"Piper执行失败: 未能解析输出时长。输出: {result.stdout[:500]}"
                )

            return output_path, duration

        except subprocess.TimeoutExpired:
            raise RuntimeError("Piper执行超时（300秒）")
        except Exception as e:
            raise RuntimeError(f"Piper执行失败: {e}")


class XTTSTTSProvider(TTSProvider):
    """XTTS V2 音色模仿TTS"""

    def __init__(self, reference_wav: str = None, model_path: str = None):
        self.reference_wav = reference_wav
        # 使用config.py中的配置
        self.model_path = model_path or str(XTTS_MODEL_PATH)
        self._python_exe = str(XTTS_PY)

    def synthesize(
        self, text: str, output_path: str, reference_wav: str = None
    ) -> Tuple[str, float]:
        ref_wav = reference_wav or self.reference_wav
        if not ref_wav:
            raise ValueError("XTTS需要参考音频文件 (reference_wav)")

        if not Path(ref_wav).exists():
            raise FileNotFoundError(f"参考音频不存在: {ref_wav}")

        # 使用subprocess调用xtts-v2环境的Python执行XTTS
        import subprocess

        # 构建xtts环境路径
        xtts_base = Path(self.model_path)
        xtts_site_packages = xtts_base / "env" / "Lib" / "site-packages"

        script = f'''
import sys
sys.path.insert(0, r"{xtts_site_packages}")
from TTS.api import TTS
import librosa
import numpy as np
import torch

print("XTTS进度: 正在加载模型...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
# 使用新API将模型移到GPU
tts.to("cuda")
print("XTTS进度: 模型加载完成，正在处理参考音频...")

# 检查参考音频时长 (librosa 0.10+ 使用 path 参数)
ref_duration = librosa.get_duration(path={repr(ref_wav)})
print(f"XTTS进度: 参考音频时长 {{ref_duration:.1f}} 秒")

# XTTS 通常需要 3-30 秒的参考音频，过长可能会影响效果
if ref_duration > 30:
    print(f"警告: 参考音频过长({{ref_duration:.1f}}秒)，建议使用3-30秒的音频")

print("XTTS进度: 正在合成语音，这可能需要几分钟...")
tts.tts_to_file(
    text={repr(text)},
    speaker_wav={repr(ref_wav)},
    language="en",
    file_path={repr(output_path)}
)
print("XTTS进度: 语音合成完成，正在处理...")

duration = librosa.get_duration(path={repr(output_path)})
print(f"XTTS完成: 生成的音频时长 {{duration:.1f}} 秒")
'''

        try:
            result = subprocess.run(
                [self._python_exe, "-c", script],
                capture_output=True,
                text=True,
                timeout=900,
            )

            # 打印 XTTS 的进度输出
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"  [XTTS] {line}")

            if result.returncode != 0:
                raise RuntimeError(f"XTTS执行失败: {result.stderr[:2000]}")

            # 解析输出获取时长 - 从输出中找最后一个 "X.X 秒" 格式
            duration = 0.0
            import re

            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                # 找 "XTTS完成: 生成的音频时长 X.X 秒" 格式
                match = re.search(r"生成的音频时长\s*(\d+\.?\d*)\s*秒", line)
                if match:
                    duration = float(match.group(1))
                    # 不立即返回，继续找后面的（可能有多个）

            if duration == 0.0:
                raise RuntimeError(
                    f"XTTS执行失败: 未能解析输出时长。输出: {result.stdout[:500]}"
                )

            return output_path, duration

        except subprocess.TimeoutExpired:
            raise RuntimeError("XTTS执行超时（900秒）")
        except Exception as e:
            raise RuntimeError(f"XTTS执行失败: {e}")


class OnlineTTSProvider(TTSProvider):
    """在线TTS API"""

    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG.get("tts_api", {})
        self._client = None

    def _get_client(self):
        if self._client is None:
            provider = self.api_config.get("provider", "edge")

            if provider == "edge":
                try:
                    import edge_tts

                    self._client = edge_tts
                except ImportError:
                    raise ImportError("请安装edge-tts: pip install edge-tts")
            elif provider == "openai":
                try:
                    from openai import OpenAI

                    self._client = OpenAI(api_key=self.api_config.get("api_key", ""))
                except ImportError:
                    raise ImportError("请安装openai: pip install openai")
            elif provider == "azure":
                try:
                    import azure.cognitiveservices.speech as speech

                    self._client = speech
                except ImportError:
                    raise ImportError("请安装azure-cognitiveservices-speech")
            elif provider == "minimax":
                # MiniMax TTS uses direct HTTP API
                pass  # No special client needed

        return self._client

    def synthesize(
        self, text: str, output_path: str, method: str = None
    ) -> Tuple[str, float]:
        # 优先使用传入的method参数，否则使用api_config中的provider
        # 这修复了kokoro/minimax选择不生效的问题
        provider = method if method else self.api_config.get("provider", "edge")

        if provider == "edge":
            return self._synthesize_edge(text, output_path)
        elif provider == "openai":
            return self._synthesize_openai(text, output_path)
        elif provider == "minimax":
            return self._synthesize_minimax(text, output_path)
        elif provider == "kokoro":
            return self._synthesize_kokoro(text, output_path)
        else:
            raise ValueError(f"不支持的TTS provider: {provider}")

    def _synthesize_edge(self, text: str, output_path: str) -> Tuple[str, float]:
        try:
            import edge_tts
            import asyncio

            voice = self.api_config.get("voice", "en-US-AriaNeural")

            async def run():
                tts = edge_tts.Communicate(text, voice)
                await tts.save(output_path)

            # 直接使用asyncio.run()（因为这个方法本身可能在异步上下文中被调用）
            asyncio.run(run())

            # 计算时长
            import librosa

            duration = librosa.get_duration(path=output_path)

            return output_path, duration
        except ImportError:
            raise RuntimeError("Edge TTS未安装，请运行: pip install edge-tts")

    def _synthesize_kokoro(self, text: str, output_path: str) -> Tuple[str, float]:
        """Kokoro TTS 合成 - 使用subprocess调用专属Python环境"""
        import subprocess
        import numpy as np

        # Kokoro Python环境路径
        kokoro_python = r"D:\_BiShe\kokoro-tts\env\Scripts\python.exe"

        # 获取音色设置 - 优先使用kokoro_voice，其次使用voice，最后默认af_heart
        # 注意：如果config中的值为None，需要使用fallback
        kokoro_voice = self.api_config.get("kokoro_voice")
        voice_value = self.api_config.get("voice")

        if kokoro_voice and kokoro_voice.strip():
            voice = kokoro_voice
        elif voice_value and voice_value.strip():
            voice = voice_value
        else:
            voice = "af_heart"

        speed = self.api_config.get("speed", 1.0)

        # 验证音色是否为有效的Kokoro音色
        valid_kokoro_voices = [
            "af_heart",
            "af_bella",
            "af_sarah",
            "af_sky",
            "af_nicole",
            "af_nova",
            "af_alloy",
            "af_aoede",
            "af_jessica",
            "af_kore",
            "af_river",
            "am_adam",
            "am_michael",
            "am_echo",
            "am_eric",
            "am_fenrir",
            "am_liam",
            "am_onyx",
            "am_puck",
            "am_santa",
        ]
        if voice not in valid_kokoro_voices:
            print(f"[Kokoro] 警告: 音色 '{voice}' 不是标准Kokoro音色，使用默认af_heart")
            voice = "af_heart"

        print(f"[Kokoro] 使用音色: {voice}")

        # 构建内联脚本
        script = f"""
from kokoro import KPipeline
import soundfile as sf
import numpy as np

pipeline = KPipeline(lang_code='a')
generator = pipeline({repr(text)}, voice={repr(voice)}, speed={speed})

all_audio = []
for _, _, audio in generator:
    all_audio.append(audio)

combined = np.concatenate(all_audio)
sf.write({repr(output_path)}, combined, 24000)
print("KOKORO_OK")
"""

        result = subprocess.run(
            [kokoro_python, "-c", script], capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            raise RuntimeError(f"Kokoro TTS生成失败: {result.stderr}")

        if not Path(output_path).exists():
            raise RuntimeError(f"Kokoro TTS未生成输出文件")

        # 计算时长
        import librosa

        duration = librosa.get_duration(path=output_path)

        return output_path, duration

    def _synthesize_edge(self, text: str, output_path: str) -> Tuple[str, float]:
        client = self._get_client()

        response = client.audio.speech.create(
            model="tts-1", voice=self.api_config.get("voice", "alloy"), input=text
        )

        response.stream_to_file(output_path)

        # 计算时长
        import librosa

        duration = librosa.get_duration(filename=output_path)

        return output_path, duration

    def _synthesize_minimax(self, text: str, output_path: str) -> Tuple[str, float]:
        """MiniMax TTS 合成"""
        import requests
        import json

        api_key = self.api_config.get("api_key", "")
        model = self.api_config.get("model", "speech-02-turbo")
        voice_id = self.api_config.get("voice_id", "English_Graceful_Lady")
        base_url = self.api_config.get("base_url", "https://api.minimaxi.com")

        url = f"{base_url}/v1/t2a_v2"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            raise RuntimeError(
                f"MiniMax TTS API错误: {response.status_code} - {response.text}"
            )

        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise RuntimeError(
                f"MiniMax TTS合成失败: {result.get('base_resp', {}).get('status_msg', '未知错误')}"
            )

        # 获取hex音频数据
        audio_hex = result.get("data", {}).get("audio")
        if not audio_hex:
            raise RuntimeError("MiniMax TTS返回的音频数据为空")

        # 将hex转换为音频文件
        audio_data = bytes.fromhex(audio_hex)

        # MiniMax返回的是mp3格式，强制使用.mp3扩展名
        output_path_mp3 = str(Path(output_path).with_suffix(".mp3"))

        with open(output_path_mp3, "wb") as f:
            f.write(audio_data)

        # 计算时长
        import librosa

        duration = librosa.get_duration(filename=output_path_mp3)

        return output_path_mp3, duration


class WERDetector:
    """语音识别准确度检测 (Word Error Rate)"""

    def __init__(self, model_size: str = "small.en"):
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                # 直接使用模型名称，让faster-whisper自动从HuggingFace下载并缓存
                # 不再尝试使用本地模型目录
                self._model = WhisperModel(
                    self.model_size, device="cuda", compute_type="float16"
                )
            except Exception as e:
                raise RuntimeError(f"加载Whisper模型失败: {e}")

    def transcribe(self, audio_path: str) -> Tuple[str, List[Dict]]:
        """
        转录音频

        Returns:
            Tuple[str, List[Dict]]: (识别文本, 分段信息列表)
        """
        self._load_model()

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        segments, info = self._model.transcribe(audio_path, language="en")

        full_text = ""
        segment_list = []

        for segment in segments:
            full_text += segment.text
            segment_list.append(
                {"start": segment.start, "end": segment.end, "text": segment.text}
            )

        return full_text.strip(), segment_list

    def _strip_punctuation(self, word: str) -> str:
        """去除单词首尾的标点符号"""
        import string

        # 去除首部标点
        while word and word[0] in string.punctuation:
            word = word[1:]
        # 去除尾部标点
        while word and word[-1] in string.punctuation:
            word = word[:-1]
        return word

    def _tokenize(self, text: str) -> list:
        """分词并去除标点符号"""
        words = text.lower().split()
        return [self._strip_punctuation(w) for w in words if self._strip_punctuation(w)]

    def calculate_wer(self, reference: str, hypothesis: str) -> WERResult:
        """
        计算WER (Word Error Rate)

        WER = (S + D + I) / N
        其中 S=替换次数, D=删除次数, I=插入次数, N=参考词数

        注意：分词时会去除标点符号，只比较单词本身
        """
        ref_words = self._tokenize(reference)
        hyp_words = self._tokenize(hypothesis)

        # 简单的词错误率计算
        n = len(ref_words)
        if n == 0:
            return WERResult(
                wer=0.0, wer_percentage=0.0, total_words=0, errors=0, details=[]
            )

        # 动态规划计算编辑距离
        d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j

        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i - 1] == hyp_words[j - 1]:
                    d[i][j] = d[i - 1][j - 1]
                else:
                    d[i][j] = min(d[i - 1][j - 1], d[i - 1][j], d[i][j - 1]) + 1

        errors = d[len(ref_words)][len(hyp_words)]
        wer = errors / n

        return WERResult(
            wer=wer, wer_percentage=wer * 100, total_words=n, errors=errors, details=[]
        )

    def evaluate(self, audio_path: str, reference_text: str) -> WERResult:
        """
        评估音频与参考文本的匹配度

        Args:
            audio_path: 音频文件路径
            reference_text: 参考文本

        Returns:
            WERResult: WER评估结果
        """
        hypothesis, _ = self.transcribe(audio_path)
        return self.calculate_wer(reference_text, hypothesis)


class TTSManager:
    """TTS管理器 - 统一接口"""

    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG
        online_provider = OnlineTTSProvider(self.api_config.get("tts_api"))
        self.providers = {
            "piper": PiperTTSProvider(),
            "xtts": XTTSTTSProvider(),
            "online": online_provider,
            "minimax": online_provider,  # MiniMax使用OnlineTTSProvider
            "kokoro": online_provider,  # Kokoro使用OnlineTTSProvider
        }
        self.wer_detector = WERDetector()

    def synthesize(
        self,
        text: str,
        method: str = "piper",
        output_filename: str = None,
        reference_wav: str = None,
        wer_threshold: float = None,
    ) -> TTSResult:
        """
        合成语音并进行WER检测

        Args:
            text: 输入文本
            method: TTS方法 ("piper", "xtts", "online")
            output_filename: 输出文件名
            reference_wav: 参考音频 (用于xtts)
            wer_threshold: WER阈值，None则使用config中的默认值

        Returns:
            TTSResult: TTS结果
        """
        if method not in self.providers:
            raise ValueError(f"未知的TTS方法: {method}")

        provider = self.providers[method]

        # 生成输出路径
        if not output_filename:
            hash_str = hashlib.md5(text.encode()).hexdigest()[:8]
            output_filename = f"tts_{method}_{hash_str}.wav"

        # 如果 output_filename 是完整路径，直接使用
        if Path(output_filename).parent != Path("."):
            output_path = str(Path(output_filename).resolve())
        else:
            output_dir = OUTPUT_DIR / "audio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / output_filename)

        # 合成语音
        try:
            if method == "xtts":
                audio_path, duration = provider.synthesize(
                    text, output_path, reference_wav
                )
            else:
                # 传递method参数让OnlineTTSProvider知道使用哪个TTS引擎
                audio_path, duration = provider.synthesize(
                    text, output_path, method=method
                )
        except Exception as e:
            return TTSResult(audio_path="", duration=0, success=False, error_msg=str(e))

        # WER检测
        wer_result = self._check_wer_with_retry(
            text, audio_path, method, provider, reference_wav, wer_threshold
        )

        return TTSResult(
            audio_path=wer_result.get("audio_path", audio_path),
            duration=duration,
            wer_score=wer_result.get("wer", 1.0),
            retries=wer_result.get("retries", 0),
            success=wer_result.get("success", True),
            error_msg=wer_result.get("error", ""),
        )

    def _check_wer_with_retry(
        self,
        text: str,
        initial_audio_path: str,
        method: str,
        provider,
        reference_wav: str = None,
        wer_threshold: float = None,
    ) -> Dict[str, Any]:
        """
        检查WER并在需要时重新生成

        Args:
            text: 输入文本
            initial_audio_path: 初始音频路径
            method: TTS方法
            provider: TTS提供者
            reference_wav: 参考音频
            wer_threshold: WER阈值，None则使用config中的默认值

        Returns:
            Dict包含audio_path, wer, retries, success, error
        """
        # 使用传入的阈值或默认值
        threshold = wer_threshold if wer_threshold is not None else WER_THRESHOLD

        best_audio = initial_audio_path
        best_wer = 1.0
        retries = 0

        # 初始WER检查
        try:
            wer_result = self.wer_detector.evaluate(initial_audio_path, text)
            best_wer = wer_result.wer
        except Exception as e:
            print(f"WER检测失败: {e}")
            best_wer = 1.0

        if best_wer <= threshold:
            return {
                "audio_path": initial_audio_path,
                "wer": best_wer,
                "retries": 0,
                "success": True,
            }

        # 需要重试
        for i in range(MAX_TTS_RETRIES):
            retries = i + 1
            print(
                f"WER ({best_wer:.2%}) 超过阈值 ({threshold:.2%}), 尝试重新生成... ({retries}/{MAX_TTS_RETRIES})"
            )

            # 重新生成
            output_dir = OUTPUT_DIR / "audio"
            hash_str = hashlib.md5(f"{text}{retries}".encode()).hexdigest()[:8]
            new_audio_path = str(output_dir / f"tts_{method}_{hash_str}.wav")

            try:
                if method == "xtts":
                    provider.synthesize(text, new_audio_path, reference_wav)
                else:
                    provider.synthesize(text, new_audio_path)
            except Exception as e:
                print(f"重新生成失败: {e}")
                continue

            # 检查新音频的WER
            try:
                wer_result = self.wer_detector.evaluate(new_audio_path, text)
                current_wer = wer_result.wer
            except Exception as e:
                print(f"WER检测失败: {e}")
                current_wer = 1.0

            if current_wer < best_wer:
                best_wer = current_wer
                best_audio = new_audio_path

            if current_wer <= WER_THRESHOLD:
                return {
                    "audio_path": new_audio_path,
                    "wer": current_wer,
                    "retries": retries,
                    "success": True,
                }

        # 所有重试都失败了，返回WER最低的那个
        print(f"所有重试完成，选择WER最低的音频: {best_wer:.2%}")
        return {
            "audio_path": best_audio,
            "wer": best_wer,
            "retries": retries,
            "success": best_wer < 1.0,
            "error": "未能在重试次数内达到WER阈值",
        }

    def set_reference_audio(self, reference_wav: str):
        """设置XTTS参考音频"""
        if "xtts" in self.providers:
            self.providers["xtts"].reference_wav = reference_wav
