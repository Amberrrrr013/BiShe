"""
AI 英语演讲视频自动生成系统 - 主程序
支持完整的文本→语音→WER检测→图像处理→视频生成→字幕烧录流程
"""
import subprocess
import sys
import io
import wave
import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

# ============================================================
# 配置路径
# ============================================================
import os
PROJECT_DIR = Path(__file__).parent
MODEL_ROOT = Path(os.getenv("MODEL_ROOT", str(PROJECT_DIR.parent)))

# 各模型路径
WAV2LIP_DIR = MODEL_ROOT / "wav2lip"
SADTALKER_DIR = MODEL_ROOT / "sadtalker"
GFPGAN_DIR = MODEL_ROOT / "gfpgan"
FASTER_WHISPER_DIR = MODEL_ROOT / "faster-whisper"
PIPER_TTS_DIR = MODEL_ROOT / "piper-tts"
XTTS_DIR = MODEL_ROOT / "xtts-v2"

# Python解释器
WAV2LIP_PY = WAV2LIP_DIR / "env" / "Scripts" / "python.exe"
SADTALKER_PY = SADTALKER_DIR / "env" / "Scripts" / "python.exe"
GFPGAN_PY = GFPGAN_DIR / "env" / "Scripts" / "python.exe"
FASTER_WHISPER_PY = FASTER_WHISPER_DIR / "env" / "Scripts" / "python.exe"
PIPER_TTS_PY = PIPER_TTS_DIR / "env" / "Scripts" / "python.exe"
XTTS_PY = XTTS_DIR / "env" / "Scripts" / "python.exe"

# 测试资源
TEXT_FILE = PROJECT_DIR / "test_resourse" / "text_test.txt"
REFERENCE_AUDIO = PROJECT_DIR / "test_resourse" / "speech_test.wav"
IMAGE_FILE = PROJECT_DIR / "test_resourse" / "picture_test.jpg"

# 全局变量
current_output_dir: Optional[Path] = None
timestamp_str: str = ""


def log(msg: str, level: str = "INFO"):
    """日志输出"""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{level}] {msg}")


def create_output_dir() -> Tuple[Path, str]:
    """创建带时间戳的输出目录"""
    global current_output_dir, timestamp_str
    timestamp_str = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    output_dir = PROJECT_DIR / "output" / "non_agent" / timestamp_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建子目录
    (output_dir / "audio").mkdir(exist_ok=True)
    (output_dir / "video").mkdir(exist_ok=True)
    (output_dir / "subtitle").mkdir(exist_ok=True)
    (output_dir / "image").mkdir(exist_ok=True)
    (output_dir / "temp").mkdir(exist_ok=True)
    
    current_output_dir = output_dir
    return output_dir, timestamp_str


def get_output_dir() -> Path:
    """获取当前输出目录"""
    global current_output_dir
    if current_output_dir is None:
        create_output_dir()
    return current_output_dir


def run_command(cmd: List[str], cwd: Path = None, timeout: int = 600) -> subprocess.CompletedProcess:
    """执行命令"""
    log(f"执行: {' '.join([str(c) for c in cmd])[:80]}...")
    result = subprocess.run(
        cmd, 
        cwd=str(cwd) if cwd else None, 
        capture_output=True, 
        text=True,
        timeout=timeout
    )
    if result.returncode != 0:
        log(f"错误: {result.stderr[:200]}", "ERROR")
    return result


def read_text(path: Path) -> str:
    """读取文本文件"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ============================================================
# 文本处理模块
# ============================================================
def process_text(text_path: Path = TEXT_FILE) -> str:
    """处理文本，返回清理后的文本"""
    log("步骤1: 处理文本...")
    text = read_text(text_path)
    text = text.strip()
    log(f"  文本长度: {len(text)} 字符")
    return text


# ============================================================
# TTS模块
# ============================================================
def generate_piper_tts(text: str) -> Tuple[Path, float]:
    """
    使用Piper TTS生成音频
    返回: (音频路径, 时长秒数)
    """
    log("步骤2.1: Piper TTS生成音频...")
    
    output_dir = get_output_dir()
    audio_path = output_dir / "audio" / f"tts_piper_{timestamp_str}.wav"
    
    # Piper对长文本支持有限，限制长度
    text = text[:300].replace("'", "").replace('"', '').replace("\n", " ")
    
    # 写入临时脚本文件
    script_path = output_dir / "temp" / f"piper_script_{timestamp_str}.py"
    script_code = f'''
import sys
import io
import wave
sys.path.insert(0, r"{PIPER_TTS_DIR}")
from piper.voice import PiperVoice

voice = PiperVoice.load(r"{PIPER_TTS_DIR}/en_US-amy-medium.onnx")
buf = io.BytesIO()
with wave.open(buf, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(voice.config.sample_rate)
    voice.synthesize_wav("{text}", wav_file)

with open(r"{audio_path}", 'wb') as f:
    f.write(buf.getvalue())
print("PIPER_DONE")
'''
    script_path.parent.mkdir(exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    
    result = run_command([str(PIPER_TTS_PY), str(script_path)], timeout=120)
    
    # 清理脚本文件
    if script_path.exists():
        script_path.unlink()
    
    if result.returncode != 0:
        raise RuntimeError(f"Piper TTS失败: {result.stderr}")
    
    duration = get_audio_duration(audio_path)
    log(f"  Piper音频已生成: {audio_path.name}, 时长: {duration:.1f}s")
    return audio_path, duration


def generate_xtts_tts(text: str, ref_audio: Path = REFERENCE_AUDIO) -> Tuple[Path, float]:
    """
    使用XTTS V2音色克隆生成音频
    返回: (音频路径, 时长秒数)
    """
    log("步骤2.2: XTTS V2音色克隆生成音频...")
    
    output_dir = get_output_dir()
    audio_path = output_dir / "audio" / f"tts_xtts_{timestamp_str}.wav"
    
    # 限制文本长度
    text = text[:300].replace("'", "").replace('"', '').replace("\n", " ")
    
    # 写入临时脚本文件
    script_path = output_dir / "temp" / f"xtts_script_{timestamp_str}.py"
    script_code = f'''
import sys
sys.path.insert(0, r"{XTTS_DIR}")
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.tts_to_file(
    text="{text}",
    speaker_wav=r"{ref_audio}",
    language="en",
    file_path=r"{audio_path}"
)
print("XTTS_DONE")
'''
    script_path.parent.mkdir(exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    
    result = run_command([str(XTTS_PY), str(script_path)], timeout=300)
    
    # 清理脚本文件
    if script_path.exists():
        script_path.unlink()
    
    if result.returncode != 0:
        raise RuntimeError(f"XTTS失败: {result.stderr}")
    
    duration = get_audio_duration(audio_path)
    log(f"  XTTS音频已生成: {audio_path.name}, 时长: {duration:.1f}s")
    return audio_path, duration


def get_audio_duration(audio_path: Path) -> float:
    """获取音频时长"""
    try:
        with wave.open(str(audio_path), 'rb') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / rate
    except:
        return 0.0


# ============================================================
# WER检测模块
# ============================================================
def calculate_wer(original_text: str, audio_path: Path) -> Tuple[float, List[Dict]]:
    """
    使用faster-whisper计算WER并获取时间戳
    返回: (WER分数, 词级时间戳列表)
    """
    log("步骤3: WER质量检测...")
    
    output_dir = get_output_dir()
    words_file = output_dir / "subtitle" / f"words_timestamp_{timestamp_str}.json"
    
    # 清理参考文本
    ref_text = original_text[:500].replace("'", "").replace('"', '')
    
    # 写入临时脚本文件
    script_path = output_dir / "temp" / f"wer_script_{timestamp_str}.py"
    script_code = f'''
from faster_whisper import WhisperModel
import json

model = WhisperModel("medium.en", device="cuda", compute_type="float16")
segments, info = model.transcribe(r"{audio_path}", word_timestamps=True)

words_data = []
for segment in segments:
    for word in segment.words:
        words_data.append({{
            "word": word.word.strip(),
            "start": float(word.start),
            "end": float(word.end)
        }})

with open(r"{words_file}", "w", encoding="utf-8") as f:
    json.dump(words_data, f, ensure_ascii=False)

print(f"WER_CHECK_DONE:{{len(words_data)}}")
'''
    script_path.parent.mkdir(exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    
    result = run_command([str(FASTER_WHISPER_PY), str(script_path)], 
                         cwd=FASTER_WHISPER_DIR, timeout=180)
    
    # 清理脚本文件
    if script_path.exists():
        script_path.unlink()
    
    if result.returncode != 0:
        log(f"  WER检测失败: {result.stderr[:200]}", "WARN")
        return 1.0, []
    
    # 计算简单WER - 只比较单词数量，去除标点符号
    with open(words_file, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    
    transcribed_words = [w["word"] for w in words_data]
    # 清理参考文本中的标点符号，只保留单词
    import re
    ref_words = re.findall(r'[a-zA-Z]+', ref_text.lower())
    
    # 计算词数差异率
    diff = abs(len(ref_words) - len(transcribed_words))
    wer = diff / max(len(ref_words), 1)
    wer = min(wer, 1.0)
    
    log(f"  参考词数: {len(ref_words)}, 转录音词数: {len(transcribed_words)}")
    
    log(f"  WER评估: {wer:.2%}, 获取到 {len(words_data)} 个词的时间戳")
    return wer, words_data


def re_generate_tts_with_retry(text: str, method: str = "piper", max_retries: int = 3) -> Tuple[Path, float, int]:
    """
    带重试的TTS生成
    返回: (音频路径, 时长, 重试次数)
    """
    for attempt in range(1, max_retries + 1):
        log(f"  TTS生成尝试 {attempt}/{max_retries}...")
        
        try:
            if method == "piper":
                audio_path, duration = generate_piper_tts(text)
            else:
                audio_path, duration = generate_xtts_tts(text)
            
            # WER检测
            wer, words_data = calculate_wer(text, audio_path)
            
            if wer < 0.3:  # WER小于30%认为可接受
                log(f"  TTS质量合格 (WER={wer:.2%})")
                return audio_path, duration, attempt - 1
            
            log(f"  TTS质量不合格 (WER={wer:.2%}), 重新生成...")
            
        except Exception as e:
            log(f"  生成失败: {e}", "ERROR")
        
        if attempt < max_retries:
            log(f"  等待2秒后重试...")
            import time
            time.sleep(2)
    
    log(f"  达到最大重试次数，使用最后生成的音频", "WARN")
    return audio_path, duration, max_retries - 1


# ============================================================
# 图像处理模块
# ============================================================
def enhance_image_gfpgan(image_path: Path) -> Path:
    """
    使用GFPGAN增强图像
    返回: 增强后的图像路径
    """
    log("步骤4: GFPGAN图像增强...")
    
    output_dir = get_output_dir()
    enhanced_path = output_dir / "image" / f"enhanced_{timestamp_str}.jpg"
    
    # 创建GFPGAN输出目录
    gfpgan_output = GFPGAN_DIR / "outputs" / timestamp_str
    gfpgan_output.mkdir(parents=True, exist_ok=True)
    
    # 写入临时脚本文件
    script_path = output_dir / "temp" / f"gfpgan_script_{timestamp_str}.py"
    script_code = f'''
import sys
sys.path.insert(0, r"{GFPGAN_DIR}")
from inference_gfpgan import GFPGANer

model = GFPGANer(
    model_path=r"{GFPGAN_DIR}/GFPGANv1.4.pth",
    upscale=2,
    arch='clean',
    channel_multiplier=2
)

import cv2
img = cv2.imread(r"{image_path}")
_, _, restored = model.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
cv2.imwrite(r"{enhanced_path}", restored)
print("GFPGAN_DONE")
'''
    script_path.parent.mkdir(exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    
    result = run_command([str(GFPGAN_PY), str(script_path)], cwd=GFPGAN_DIR, timeout=300)
    
    # 清理脚本文件
    if script_path.exists():
        script_path.unlink()
    
    if result.returncode == 0 and enhanced_path.exists():
        log(f"  图像增强完成: {enhanced_path.name}")
        return enhanced_path
    else:
        log(f"  GFPGAN失败，使用原图", "WARN")
        return image_path


# ============================================================
# 视频生成模块
# ============================================================
def generate_wav2lip_video(image_path: Path, audio_path: Path) -> Path:
    """
    使用Wav2Lip生成唇形同步视频
    """
    log("步骤5.1: Wav2Lip生成视频...")
    
    output_dir = get_output_dir()
    video_path = output_dir / "video" / f"wav2lip_{timestamp_str}.mp4"
    
    checkpoint = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"
    
    cmd = [
        str(WAV2LIP_PY),
        str(WAV2LIP_DIR / "inference.py"),
        "--checkpoint_path", str(checkpoint),
        "--face", str(image_path),
        "--audio", str(audio_path),
        "--outfile", str(video_path)
    ]
    
    result = run_command(cmd, cwd=WAV2LIP_DIR, timeout=600)
    
    if result.returncode == 0 and video_path.exists():
        log(f"  Wav2Lip视频生成成功: {video_path.name}")
        return video_path
    else:
        raise RuntimeError(f"Wav2Lip失败: {result.stderr}")


def generate_sadtalker_video(image_path: Path, audio_path: Path) -> Path:
    """
    使用SadTalker生成头部运动视频
    """
    log("步骤5.2: SadTalker生成视频...")
    
    output_dir = get_output_dir()
    temp_dir = output_dir / "temp" / "sadtalker"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    video_path = output_dir / "video" / f"sadtalker_{timestamp_str}.mp4"
    
    cmd = [
        str(SADTALKER_PY),
        str(SADTALKER_DIR / "inference.py"),
        "--driven_audio", str(audio_path),
        "--source_image", str(image_path),
        "--result_dir", str(temp_dir),
        "--still",
        "--preprocess", "crop"
    ]
    
    result = run_command(cmd, cwd=SADTALKER_DIR, timeout=1200)
    
    if result.returncode != 0:
        raise RuntimeError(f"SadTalker失败: {result.stderr}")
    
    # 查找生成的视频
    mp4_files = list(temp_dir.glob("*.mp4"))
    if mp4_files:
        latest_mp4 = max(mp4_files, key=lambda p: p.stat().st_mtime)
        shutil.move(str(latest_mp4), str(video_path))
        log(f"  SadTalker视频生成成功: {video_path.name}")
        return video_path
    else:
        raise RuntimeError("SadTalker未生成视频文件")


# ============================================================
# 字幕生成模块
# ============================================================
def generate_srt_subtitle(words_data: List[Dict], output_path: Path) -> Path:
    """从词级时间戳生成SRT字幕文件"""
    log("步骤6: 生成SRT字幕...")
    
    if not words_data:
        log("  无时间戳数据，跳过字幕生成", "WARN")
        return None
    
    def format_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    lines = []
    words_per_line = 8
    current_line = []
    current_start = None
    
    for word_info in words_data:
        word = word_info["word"]
        start = word_info["start"]
        end = word_info["end"]
        
        current_line.append(word)
        if current_start is None:
            current_start = start
        
        if len(current_line) >= words_per_line:
            lines.append({
                "text": " ".join(current_line),
                "start": current_start,
                "end": end
            })
            current_line = []
            current_start = None
    
    if current_line:
        lines.append({
            "text": " ".join(current_line),
            "start": current_start,
            "end": words_data[-1]["end"]
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(line['start'])} --> {format_srt_time(line['end'])}\n")
            f.write(f"{line['text']}\n\n")
    
    log(f"  字幕文件已生成: {output_path.name}")
    return output_path


def burn_subtitle(video_path: Path, srt_path: Path, output_path: Path) -> Path:
    """
    使用FFmpeg将字幕烧录到视频
    """
    log("步骤7: 烧录字幕到视频...")
    
    # 切换到视频所在目录，使用相对路径
    video_dir = video_path.parent
    video_name = video_path.name
    srt_name = srt_path.name
    
    # 复制字幕到视频目录
    local_srt = video_dir / srt_name
    shutil.copy(str(srt_path), str(local_srt))
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_name,
        "-vf", f"subtitles={srt_name}",
        "-c:a", "copy",
        output_path.name
    ]
    
    result = subprocess.run(cmd, cwd=str(video_dir), capture_output=True, text=True, timeout=120)
    
    # 清理临时字幕文件
    if local_srt.exists():
        local_srt.unlink()
    
    if result.returncode == 0 and output_path.exists():
        log(f"  字幕视频生成成功: {output_path.name}")
        return output_path
    else:
        log(f"  FFmpeg字幕烧录失败: {result.stderr[:200]}", "ERROR")
        return video_path  # 返回原视频


# ============================================================
# 完整流程
# ============================================================
def run_full_pipeline(
    text_path: Path = TEXT_FILE,
    image_path: Path = IMAGE_FILE,
    ref_audio: Path = REFERENCE_AUDIO,
    use_xtts: bool = False,
    use_sadtalker: bool = False,
    use_gfpgan: bool = False,
    use_subtitle: bool = True
) -> Dict[str, Any]:
    """
    运行完整视频生成流程
    
    返回: 包含所有生成文件路径的字典
    """
    log("="*60)
    log("AI 英语演讲视频生成系统")
    log("="*60)
    
    # 创建输出目录
    output_dir, ts = create_output_dir()
    log(f"输出目录: {output_dir}")
    
    results = {
        "output_dir": str(output_dir),
        "timestamp": ts,
        "success": True,
        "files": {}
    }
    
    try:
        # 1. 文本处理
        text = process_text(text_path)
        results["files"]["text"] = str(text_path)
        
        # 2. TTS生成（带WER检测和重试）
        tts_method = "xtts" if use_xtts else "piper"
        audio_path, duration, retries = re_generate_tts_with_retry(text, method=tts_method)
        results["files"]["audio"] = str(audio_path)
        results["tts_retries"] = retries
        
        # 3. WER检测
        wer, words_data = calculate_wer(text, audio_path)
        results["wer"] = wer
        
        # 4. 图像处理
        if use_gfpgan:
            image_path = enhance_image_gfpgan(image_path)
        results["files"]["image"] = str(image_path)
        
        # 5. 视频生成
        if use_sadtalker:
            video_path = generate_sadtalker_video(image_path, audio_path)
        else:
            video_path = generate_wav2lip_video(image_path, audio_path)
        results["files"]["video"] = str(video_path)
        
        # 6. 字幕生成
        srt_path = None
        if use_subtitle and words_data:
            srt_path = output_dir / "subtitle" / f"subtitles_{ts}.srt"
            generate_srt_subtitle(words_data, srt_path)
            results["files"]["subtitle"] = str(srt_path)
        
        # 7. 生成两个版本视频（总是生成）
        # 7.1 无字幕版本 - 直接复制原视频
        video_no_subtitle = output_dir / "video" / f"no_subtitle_{ts}.mp4"
        shutil.copy(str(video_path), str(video_no_subtitle))
        results["files"]["video_no_subtitle"] = str(video_no_subtitle)
        
        # 7.2 带字幕版本
        if srt_path and srt_path.exists():
            video_subtitled = output_dir / "video" / f"subtitled_{ts}.mp4"
            burn_subtitle(video_path, srt_path, video_subtitled)
            results["files"]["video_subtitled"] = str(video_subtitled)
            results["files"]["final_video"] = str(video_subtitled)
        else:
            results["files"]["video_subtitled"] = str(video_path)
            results["files"]["final_video"] = str(video_path)
        
        log("="*60)
        log("视频生成完成!")
        log("="*60)
        
    except Exception as e:
        log(f"流程执行失败: {e}", "ERROR")
        results["success"] = False
        results["error"] = str(e)
    
    return results


def print_results(results: Dict[str, Any]):
    """打印结果摘要"""
    log("="*60)
    log("生成结果摘要")
    log("="*60)
    print(f"输出目录: {results['output_dir']}")
    print(f"时间戳: {results['timestamp']}")
    print(f"成功: {results['success']}")
    
    if "wer" in results:
        print(f"WER评分: {results['wer']:.2%}")
    if "tts_retries" in results:
        print(f"TTS重试次数: {results['tts_retries']}")
    
    print("\n生成的文件:")
    for key, path in results.get("files", {}).items():
        print(f"  {key}: {Path(path).name}")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI英语演讲视频生成系统")
    parser.add_argument("--xtts", action="store_true", help="使用XTTS音色克隆")
    parser.add_argument("--sadtalker", action="store_true", help="使用SadTalker")
    parser.add_argument("--gfpgan", action="store_true", help="使用GFPGAN增强")
    parser.add_argument("--no-subtitle", action="store_true", help="不添加字幕")
    parser.add_argument("--text", type=str, help="文本文件路径")
    parser.add_argument("--image", type=str, help="图像文件路径")
    parser.add_argument("--ref-audio", type=str, help="参考音频文件路径(XTTS用)")
    
    args = parser.parse_args()
    
    # 使用命令行参数或默认值
    text_path = Path(args.text) if args.text else TEXT_FILE
    image_path = Path(args.image) if args.image else IMAGE_FILE
    ref_audio = Path(args.ref_audio) if args.ref_audio else REFERENCE_AUDIO
    
    results = run_full_pipeline(
        text_path=text_path,
        image_path=image_path,
        ref_audio=ref_audio,
        use_xtts=args.xtts,
        use_sadtalker=args.sadtalker,
        use_gfpgan=args.gfpgan,
        use_subtitle=not args.no_subtitle
    )
    
    print_results(results)
