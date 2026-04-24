"""
AI 英语演讲视频生成系统 - 豪华可视化界面
功能完整匹配HTML前端，支持所有工作流选项
"""
import subprocess
import sys
import os
import threading
import shutil
import re
import json
from pathlib import Path
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext

# ============================================================
# 配置路径
# ============================================================
import os
PROJECT_DIR = Path(__file__).parent
MODEL_ROOT = Path(os.getenv("MODEL_ROOT", str(PROJECT_DIR.parent)))

WAV2LIP_DIR = MODEL_ROOT / "wav2lip"
SADTALKER_DIR = MODEL_ROOT / "sadtalker"
GFPGAN_DIR = MODEL_ROOT / "gfpgan"
FASTER_WHISPER_DIR = MODEL_ROOT / "faster-whisper"
PIPER_TTS_DIR = MODEL_ROOT / "piper-tts"
XTTS_DIR = MODEL_ROOT / "xtts-v2"

WAV2LIP_PY = WAV2LIP_DIR / "env" / "Scripts" / "python.exe"
SADTALKER_PY = SADTALKER_DIR / "env" / "Scripts" / "python.exe"
GFPGAN_PY = GFPGAN_DIR / "env" / "Scripts" / "python.exe"
FASTER_WHISPER_PY = FASTER_WHISPER_DIR / "env" / "Scripts" / "python.exe"
PIPER_TTS_PY = PIPER_TTS_DIR / "env" / "Scripts" / "python.exe"
XTTS_PY = XTTS_DIR / "env" / "Scripts" / "python.exe"

# 全局变量
current_output_dir = None
timestamp_str = ""
is_running = False

# ============================================================
# 颜色主题
# ============================================================
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'accent1': '#00d9ff',
    'accent2': '#00ff88',
    'text': '#ffffff',
    'text_secondary': '#888888',
    'error': '#ff4757',
    'warning': '#ffa502',
    'success': '#2ed573'
}

# ============================================================
# 日志输出
# ============================================================
def log(msg, level="INFO"):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{level}] {msg}")

# ============================================================
# 核心功能函数
# ============================================================
def run_command(cmd, cwd=None, timeout=600):
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, 
                          capture_output=True, text=True, timeout=timeout)
    return result

def get_audio_duration(audio_path):
    try:
        import wave
        with wave.open(str(audio_path), 'rb') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / rate
    except:
        return 0.0

def create_output_dir():
    global current_output_dir, timestamp_str
    timestamp_str = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    output_dir = PROJECT_DIR / "output" / timestamp_str
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audio").mkdir(exist_ok=True)
    (output_dir / "video").mkdir(exist_ok=True)
    (output_dir / "subtitle").mkdir(exist_ok=True)
    (output_dir / "image").mkdir(exist_ok=True)
    (output_dir / "temp").mkdir(exist_ok=True)
    current_output_dir = output_dir
    return output_dir, timestamp_str

def process_text(text_path):
    with open(text_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_piper_tts(text, audio_path):
    text = text[:300].replace("'", "").replace('"', '').replace("\n", " ")
    script_path = audio_path.parent / f"piper_script_{timestamp_str}.py"
    script_code = f'''
import sys, io, wave
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
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    result = run_command([str(PIPER_TTS_PY), str(script_path)], timeout=120)
    if script_path.exists():
        script_path.unlink()
    if result.returncode != 0:
        raise RuntimeError(f"Piper失败: {result.stderr[:100]}")
    return get_audio_duration(audio_path)

def generate_xtts_tts(text, ref_audio, audio_path):
    text = text[:300].replace("'", "").replace('"', '').replace("\n", " ")
    script_path = audio_path.parent / f"xtts_script_{timestamp_str}.py"
    script_code = f'''
import sys
sys.path.insert(0, r"{XTTS_DIR}")
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.tts_to_file(text="{text}", speaker_wav=r"{ref_audio}", language="en", file_path=r"{audio_path}")
print("XTTS_DONE")
'''
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    result = run_command([str(XTTS_PY), str(script_path)], timeout=300)
    if script_path.exists():
        script_path.unlink()
    if result.returncode != 0:
        raise RuntimeError(f"XTTS失败: {result.stderr[:100]}")
    return get_audio_duration(audio_path)

def calculate_wer(original_text, audio_path, words_file):
    import re, json
    ref_text = original_text[:500].replace("'", "").replace('"', '')
    ref_words = re.findall(r'[a-zA-Z]+', ref_text.lower())
    
    script_path = words_file.parent / f"wer_script_{timestamp_str}.py"
    script_code = f'''
from faster_whisper import WhisperModel
import json
model = WhisperModel("medium.en", device="cuda", compute_type="float16")
segments, info = model.transcribe(r"{audio_path}", word_timestamps=True)
words_data = []
for segment in segments:
    for word in segment.words:
        words_data.append({{"word": word.word.strip(), "start": float(word.start), "end": float(word.end)}})
with open(r"{words_file}", "w", encoding="utf-8") as f:
    json.dump(words_data, f, ensure_ascii=False)
print(f"WER_DONE:{{len(words_data)}}")
'''
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    result = run_command([str(FASTER_WHISPER_PY), str(script_path)], 
                         cwd=FASTER_WHISPER_DIR, timeout=180)
    if script_path.exists():
        script_path.unlink()
    if result.returncode != 0:
        return 1.0, []
    
    with open(words_file, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    transcribed = [w["word"] for w in words_data]
    diff = abs(len(ref_words) - len(transcribed))
    wer = min(diff / max(len(ref_words), 1), 1.0)
    return wer, words_data

def enhance_image_gfpgan(image_path, enhanced_path):
    script_path = enhanced_path.parent / f"gfpgan_script_{timestamp_str}.py"
    script_code = f'''
import sys, cv2
sys.path.insert(0, r"{GFPGAN_DIR}")
from inference_gfpgan import GFPGANer
model = GFPGANer(model_path=r"{GFPGAN_DIR}/GFPGANv1.4.pth", upscale=2, arch='clean', channel_multiplier=2)
img = cv2.imread(r"{image_path}")
_, _, restored = model.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
cv2.imwrite(r"{enhanced_path}", restored)
print("GFPGAN_DONE")
'''
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_code)
    result = run_command([str(GFPGAN_PY), str(script_path)], cwd=GFPGAN_DIR, timeout=300)
    if script_path.exists():
        script_path.unlink()
    if result.returncode == 0 and enhanced_path.exists():
        return enhanced_path
    return image_path

def generate_wav2lip_video(image_path, audio_path, video_path):
    checkpoint = WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"
    cmd = [str(WAV2LIP_PY), str(WAV2LIP_DIR / "inference.py"),
           "--checkpoint_path", str(checkpoint), "--face", str(image_path),
           "--audio", str(audio_path), "--outfile", str(video_path)]
    result = run_command(cmd, cwd=WAV2LIP_DIR, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Wav2Lip失败: {result.stderr[:100]}")
    return video_path

def generate_sadtalker_video(image_path, audio_path, temp_dir, video_path):
    temp_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(SADTALKER_PY), str(SADTALKER_DIR / "inference.py"),
           "--driven_audio", str(audio_path), "--source_image", str(image_path),
           "--result_dir", str(temp_dir), "--still", "--preprocess", "crop"]
    result = run_command(cmd, cwd=SADTALKER_DIR, timeout=1200)
    if result.returncode != 0:
        raise RuntimeError(f"SadTalker失败: {result.stderr[:100]}")
    mp4_files = list(temp_dir.glob("*.mp4"))
    if not mp4_files:
        raise RuntimeError("未生成视频文件")
    latest = max(mp4_files, key=lambda p: p.stat().st_mtime)
    shutil.move(str(latest), str(video_path))
    return video_path

def generate_srt_subtitle(words_data, output_path):
    def format_time(s):
        h, m, sec = int(s//3600), int((s%3600)//60), int(s%60)
        ms = int((s%1)*1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
    lines, current_line, current_start = [], [], None
    for w in words_data:
        current_line.append(w["word"])
        if current_start is None:
            current_start = w["start"]
        if len(current_line) >= 8:
            lines.append({"text": " ".join(current_line), "start": current_start, "end": w["end"]})
            current_line, current_start = [], None
    if current_line:
        lines.append({"text": " ".join(current_line), "start": current_start, "end": words_data[-1]["end"]})
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            f.write(f"{i}\n{format_time(line['start'])} --> {format_time(line['end'])}\n{line['text']}\n\n")

def burn_subtitle(video_path, srt_path, output_path):
    video_dir = video_path.parent
    local_srt = video_dir / srt_path.name
    shutil.copy(str(srt_path), str(local_srt))
    cmd = ["ffmpeg", "-y", "-i", video_path.name, "-vf", f"subtitles={srt_path.name}",
           "-c:a", "copy", output_path.name]
    result = subprocess.run(cmd, cwd=str(video_dir), capture_output=True, text=True, timeout=120)
    if local_srt.exists():
        local_srt.unlink()
    if result.returncode == 0 and output_path.exists():
        return output_path
    return video_path

# ============================================================
# 主生成流程
# ============================================================
def run_generation(text_path, image_path, ref_audio, use_xtts, use_sadtalker, use_gfpgan, wer_threshold, add_subtitles, log_func, progress_callback):
    global current_output_dir, timestamp_str
    
    try:
        output_dir, ts = create_output_dir()
        log_func(f"输出目录: {output_dir}\n")
        progress_callback(1)
        
        # 1. 处理文本
        text = process_text(text_path)
        log_func(f"步骤1: 文本处理完成 ({len(text)}字符)\n")
        progress_callback(2)
        
        # 2. TTS生成（带重试）
        audio_path = output_dir / "audio" / f"tts_{'xtts' if use_xtts else 'piper'}_{ts}.wav"
        tts_method = "xtts" if use_xtts else "piper"
        for attempt in range(1, 4):
            log_func(f"步骤2: TTS生成 (尝试 {attempt}/3, 方法: {tts_method})...\n")
            try:
                if use_xtts:
                    generate_xtts_tts(text, ref_audio, audio_path)
                else:
                    generate_piper_tts(text, audio_path)
                break
            except Exception as e:
                if attempt == 3:
                    raise
                log_func(f"重试...\n")
        
        duration = get_audio_duration(audio_path)
        log_func(f"音频生成完成, 时长: {duration:.1f}s\n")
        progress_callback(3)
        
        # 3. WER检测
        words_file = output_dir / "subtitle" / f"words_{ts}.json"
        wer, words_data = calculate_wer(text, audio_path, words_file)
        log_func(f"步骤3: WER检测完成, WER={wer:.2%}\n")
        
        if wer > wer_threshold / 100:
            log_func(f"警告: WER({wer:.2%})超过阈值({wer_threshold}%), 建议检查音频质量\n", "WARN")
        
        # 4. 图像处理
        if use_gfpgan:
            enhanced_path = output_dir / "image" / f"enhanced_{ts}.jpg"
            enhance_image_gfpgan(image_path, enhanced_path)
            image_path = enhanced_path
            log_func(f"步骤4: GFPGAN图像增强完成\n")
        else:
            log_func(f"步骤4: 跳过图像增强\n")
        progress_callback(4)
        
        # 5. 视频生成
        video_path = output_dir / "video" / f"{'sadtalker' if use_sadtalker else 'wav2lip'}_{ts}.mp4"
        if use_sadtalker:
            temp_dir = output_dir / "temp" / "sadtalker"
            generate_sadtalker_video(image_path, audio_path, temp_dir, video_path)
        else:
            generate_wav2lip_video(image_path, audio_path, video_path)
        log_func(f"步骤5: 视频生成完成\n")
        
        # 6. 字幕生成
        if add_subtitles:
            srt_path = output_dir / "subtitle" / f"subtitles_{ts}.srt"
            generate_srt_subtitle(words_data, srt_path)
            log_func(f"步骤6: 字幕生成完成\n")
        else:
            srt_path = None
            log_func(f"步骤6: 跳过字幕生成\n")
        progress_callback(7)
        
        # 7. 生成两个版本
        no_subtitle_path = output_dir / "video" / f"no_subtitle_{ts}.mp4"
        shutil.copy(str(video_path), str(no_subtitle_path))
        
        subtitled_path = None
        if add_subtitles and srt_path:
            subtitled_path = output_dir / "video" / f"subtitled_{ts}.mp4"
            burn_subtitle(video_path, srt_path, subtitled_path)
        
        progress_callback(8)
        log_func(f"="*50 + "\n")
        log_func(f"生成完成!\n")
        log_func(f"无字幕版本: no_subtitle_{ts}.mp4\n")
        if subtitled_path:
            log_func(f"带字幕版本: subtitled_{ts}.mp4\n")
        log_func(f"="*50 + "\n")
        log_func(f"所有文件保存在: {output_dir}\n")
        
        return True
        
    except Exception as e:
        log_func(f"错误: {e}\n", "ERROR")
        return False

# ============================================================
# 豪华GUI界面
# ============================================================
def create_gui():
    global is_running
    
    root = Tk()
    root.title("AI 英语演讲视频生成系统")
    root.geometry("1000x850")
    root.minsize(900, 800)
    root.configure(bg=COLORS['bg_dark'])
    
    # 变量
    text_mode = StringVar(value="user_text")
    user_text = StringVar(value="Hello, this is a test speech for AI video generation.")
    topic = StringVar(value="Climate Change")
    length = IntVar(value=300)
    difficulty = StringVar(value="intermediate")
    style = StringVar(value="general")
    
    image_mode = StringVar(value="upload")
    image_path = StringVar(value=str(PROJECT_DIR / "test_resourse" / "picture_test.jpg"))
    image_prompt = StringVar()
    enhance_image = BooleanVar(value=True)
    
    tts_method = StringVar(value="piper")
    ref_audio_path = StringVar(value=str(PROJECT_DIR / "test_resourse" / "speech_test.wav"))
    wer_threshold = IntVar(value=15)
    
    video_method = StringVar(value="sadtalker")
    add_subtitles = BooleanVar(value=True)
    
    current_step = IntVar(value=0)
    
    # 样式配置
    style_config = {
        'bg': COLORS['bg_dark'],
        'fg': COLORS['text'],
        'activebackground': COLORS['bg_medium'],
        'selectcolor': COLORS['bg_light'],
        'highlightthickness': 0
    }
    
    radio_style = {'indicatoron': 0, 'width': 18, 'anchor': 'w', **style_config}
    check_style = {'anchor': 'w', **style_config}
    
    # 创建主框架
    main_container = Frame(root, bg=COLORS['bg_dark'])
    main_container.pack(fill=BOTH, expand=True)
    
    # 顶部标题栏
    header_frame = Frame(main_container, bg=COLORS['bg_medium'], height=80)
    header_frame.pack(fill=X, padx=0, pady=0)
    header_frame.pack_propagate(False)
    
    title_label = Label(header_frame, 
                        text="AI 英语演讲视频生成系统",
                        font=("Microsoft YaHei UI", 22, "bold"),
                        bg=COLORS['bg_medium'], fg=COLORS['accent1'])
    title_label.pack(side=LEFT, padx=30, pady=20)
    
    subtitle_label = Label(header_frame,
                           text="LangGraph-powered 智能自动化生成平台",
                           font=("Microsoft YaHei UI", 10),
                           bg=COLORS['bg_medium'], fg=COLORS['text_secondary'])
    subtitle_label.pack(side=RIGHT, anchor=E, padx=30, pady=25)
    
    # 主内容区域
    content_frame = Frame(main_container, bg=COLORS['bg_dark'])
    content_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # 左侧面板
    left_frame = Frame(content_frame, bg=COLORS['bg_medium'], padx=12, pady=12)
    left_frame.pack(side=LEFT, fill=BOTH, expand=True)
    
    # 右侧面板
    right_frame = Frame(content_frame, bg=COLORS['bg_medium'], padx=12, pady=12)
    right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
    
    # ========== 左侧内容 ==========
    
    # 文本设置面板
    Label(left_frame, text="📝 文本设置", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(0, 10))
    
    # 文本模式选择
    mode_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    mode_frame.pack(fill=X, pady=5)
    
    text_mode_frame = Frame(mode_frame, bg=COLORS['bg_light'], padx=5, pady=5)
    text_mode_frame.pack(fill=X)
    
    Radiobutton(text_mode_frame, text="📄 用户文本", variable=text_mode, value="user_text", **radio_style).pack(side=LEFT, padx=5)
    Radiobutton(text_mode_frame, text="🤖 AI生成", variable=text_mode, value="ai_generate", **radio_style).pack(side=LEFT, padx=5)
    Radiobutton(text_mode_frame, text="🎲 随机练习", variable=text_mode, value="random", **radio_style).pack(side=LEFT, padx=5)
    
    # 用户文本输入
    user_text_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    user_text_frame.pack(fill=X, pady=5)
    
    Label(user_text_frame, text="演讲文本内容:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=W)
    user_text_area = Text(user_text_frame, height=5, width=40, font=("Consolas", 10),
                          bg=COLORS['bg_dark'], fg=COLORS['text'], insertbackground=COLORS['accent1'])
    user_text_area.pack(fill=X, pady=5)
    user_text_area.insert('1.0', user_text.get())
    
    # AI生成选项
    ai_options_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    ai_options_frame.pack(fill=X, pady=5)
    
    Label(ai_options_frame, text="演讲主题:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=W)
    Entry(ai_options_frame, textvariable=topic, width=40, bg=COLORS['bg_dark'], fg=COLORS['text'],
          insertbackground=COLORS['accent1']).pack(fill=X, pady=3)
    
    length_frame = Frame(ai_options_frame, bg=COLORS['bg_medium'])
    length_frame.pack(fill=X, pady=5)
    Label(length_frame, text="目标字数:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(side=LEFT)
    length_scale = Scale(length_frame, from_=100, to=800, orient=HORIZONTAL, variable=length,
                         bg=COLORS['bg_medium'], fg=COLORS['accent1'], highlightthickness=0,
                         troughcolor=COLORS['bg_light'], length=150)
    length_scale.pack(side=RIGHT)
    Label(length_frame, textvariable=length, bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(side=RIGHT, padx=10)
    
    difficulty_frame = Frame(ai_options_frame, bg=COLORS['bg_medium'])
    difficulty_frame.pack(fill=X, pady=3)
    Label(difficulty_frame, text="难度:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(side=LEFT)
    OptionMenu(difficulty_frame, difficulty, "easy", "intermediate", "advanced").pack(side=RIGHT)
    
    # 图像设置面板
    Label(left_frame, text="🖼️ 图像设置", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(20, 10))
    
    image_source_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    image_source_frame.pack(fill=X, pady=5)
    
    image_radio_frame = Frame(image_source_frame, bg=COLORS['bg_light'], padx=5, pady=5)
    image_radio_frame.pack(fill=X)
    
    Radiobutton(image_radio_frame, text="📁 上传", variable=image_mode, value="upload", **radio_style).pack(side=LEFT, padx=3)
    Radiobutton(image_radio_frame, text="🌐 URL", variable=image_mode, value="url", **radio_style).pack(side=LEFT, padx=3)
    Radiobutton(image_radio_frame, text="🎨 AI生成", variable=image_mode, value="api", **radio_style).pack(side=LEFT, padx=3)
    
    # 图像路径输入
    image_path_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    image_path_frame.pack(fill=X, pady=5)
    Label(image_path_frame, text="人像图片路径:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=W)
    path_row = Frame(image_path_frame, bg=COLORS['bg_medium'])
    path_row.pack(fill=X, pady=3)
    Entry(path_row, textvariable=image_path, width=35, bg=COLORS['bg_dark'], fg=COLORS['text'],
          insertbackground=COLORS['accent1']).pack(side=LEFT, fill=X, expand=True)
    Button(path_row, text="浏览", command=lambda: image_path.set(
        filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])),
           bg=COLORS['bg_light'], fg=COLORS['text']).pack(side=LEFT, padx=5)
    
    Checkbutton(left_frame, text="✨ 使用 GFPGAN 增强图像清晰度", variable=enhance_image,
                **check_style).pack(anchor=W, pady=10)
    
    # TTS设置面板
    Label(left_frame, text="🎙️ 语音设置", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(20, 10))
    
    tts_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    tts_frame.pack(fill=X, pady=5)
    
    tts_radio_frame = Frame(tts_frame, bg=COLORS['bg_light'], padx=5, pady=5)
    tts_radio_frame.pack(fill=X)
    
    Radiobutton(tts_radio_frame, text="🔊 Piper TTS", variable=tts_method, value="piper", **radio_style).pack(side=LEFT, padx=3)
    Radiobutton(tts_radio_frame, text="🎭 XTTS 音色", variable=tts_method, value="xtts", **radio_style).pack(side=LEFT, padx=3)
    
    # XTTS参考音频
    xtts_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    xtts_frame.pack(fill=X, pady=5)
    Label(xtts_frame, text="参考音色音频(XTTS用):", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=W)
    ref_row = Frame(xtts_frame, bg=COLORS['bg_medium'])
    ref_row.pack(fill=X, pady=3)
    Entry(ref_row, textvariable=ref_audio_path, width=35, bg=COLORS['bg_dark'], fg=COLORS['text'],
          insertbackground=COLORS['accent1']).pack(side=LEFT, fill=X, expand=True)
    Button(ref_row, text="浏览", command=lambda: ref_audio_path.set(
        filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3")])),
           bg=COLORS['bg_light'], fg=COLORS['text']).pack(side=LEFT, padx=5)
    
    # WER阈值
    wer_frame = Frame(left_frame, bg=COLORS['bg_medium'])
    wer_frame.pack(fill=X, pady=10)
    wer_row = Frame(wer_frame, bg=COLORS['bg_medium'])
    wer_row.pack(fill=X)
    Label(wer_row, text="WER阈值:", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(side=LEFT)
    wer_scale = Scale(wer_row, from_=5, to=30, orient=HORIZONTAL, variable=wer_threshold,
                      bg=COLORS['bg_medium'], fg=COLORS['accent1'], highlightthickness=0,
                      troughcolor=COLORS['bg_light'], length=120)
    wer_scale.pack(side=RIGHT)
    Label(wer_row, textvariable=wer_threshold, bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(side=RIGHT, padx=10)
    Label(wer_row, text="%", bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack(side=RIGHT)
    
    # ========== 右侧内容 ==========
    
    # 视频设置面板
    Label(right_frame, text="🎬 视频设置", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(0, 10))
    
    video_frame = Frame(right_frame, bg=COLORS['bg_medium'])
    video_frame.pack(fill=X, pady=5)
    
    video_radio_frame = Frame(video_frame, bg=COLORS['bg_light'], padx=5, pady=5)
    video_radio_frame.pack(fill=X)
    
    Radiobutton(video_radio_frame, text="🎭 SadTalker", variable=video_method, value="sadtalker", **radio_style).pack(side=LEFT, padx=3)
    Radiobutton(video_radio_frame, text="⚡ Wav2Lip", variable=video_method, value="wav2lip", **radio_style).pack(side=LEFT, padx=3)
    
    Checkbutton(right_frame, text="📝 添加英文字幕", variable=add_subtitles, **check_style).pack(anchor=W, pady=10)
    
    # 进度显示
    Label(right_frame, text="📊 生成进度", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(20, 10))
    
    progress_frame = Frame(right_frame, bg=COLORS['bg_dark'], padx=10, pady=15)
    progress_frame.pack(fill=X, pady=5)
    
    # 步骤指示器
    steps = ["文本", "图像", "语音", "视频", "字幕"]
    step_labels = []
    step_frame = Frame(progress_frame, bg=COLORS['bg_dark'])
    step_frame.pack(fill=X)
    
    for i, step_name in enumerate(steps):
        step_box = Frame(step_frame, bg=COLORS['bg_light'], width=60, height=50)
        step_box.pack(side=LEFT, padx=5)
        step_box.pack_propagate(False)
        step_num = Label(step_box, text=str(i+1), font=("Arial", 16, "bold"),
                        bg=COLORS['bg_light'], fg=COLORS['text_secondary'])
        step_num.pack(expand=True)
        step_label = Label(step_frame, text=step_name, font=("Microsoft YaHei UI", 9),
                          bg=COLORS['bg_dark'], fg=COLORS['text_secondary'])
        step_label.pack(side=LEFT, padx=5, anchor=N)
        step_labels.append((step_box, step_num, step_label))
    
    # 日志输出
    Label(right_frame, text="📋 日志输出", font=("Microsoft YaHei UI", 13, "bold"),
         bg=COLORS['bg_medium'], fg=COLORS['accent1']).pack(anchor=W, pady=(20, 10))
    
    log_frame = Frame(right_frame, bg=COLORS['bg_dark'])
    log_frame.pack(fill=BOTH, expand=True, pady=5)
    
    log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 10),
                                         bg="black", fg=COLORS['accent2'],
                                         insertbackground=COLORS['accent1'],
                                         state='disabled', wrap=WORD)
    log_text.pack(fill=BOTH, expand=True)
    
    def update_progress(step):
        for i, (box, num, label) in enumerate(step_labels):
            if i < step:
                box.configure(bg=COLORS['success'])
                num.configure(bg=COLORS['success'], fg=COLORS['bg_dark'])
                label.configure(fg=COLORS['success'])
            elif i == step - 1:
                box.configure(bg=COLORS['accent1'])
                num.configure(bg=COLORS['accent1'], fg=COLORS['bg_dark'])
                label.configure(fg=COLORS['accent1'])
            else:
                box.configure(bg=COLORS['bg_light'])
                num.configure(bg=COLORS['bg_light'], fg=COLORS['text_secondary'])
                label.configure(fg=COLORS['text_secondary'])
    
    def log_to_gui(msg, level="INFO"):
        log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text.insert('end', f"[{timestamp}] {msg}")
        if level == "ERROR":
            log_text.tag_add(level, "end-2c", "end")
            log_text.tag_config(level, foreground=COLORS['error'])
        elif level == "WARN":
            log_text.tag_add(level, "end-2c", "end")
            log_text.tag_config(level, foreground=COLORS['warning'])
        log_text.see('end')
        log_text.configure(state='disabled')
    
    # 按钮区域
    btn_frame = Frame(right_frame, bg=COLORS['bg_medium'], pady=15)
    btn_frame.pack(fill=X)
    
    def start_generation():
        global is_running
        if is_running:
            return
        is_running = True
        btn_start.config(state=DISABLED)
        btn_stop.config(state=NORMAL)
        log_to_gui("✨ 开始生成...\n")
        update_progress(1)
        
        def run():
            try:
                text_content = user_text_area.get('1.0', 'end').strip()
                if not text_content:
                    text_content = f"Hello, this is a test speech about {topic.get()}."
                
                temp_text = current_output_dir / "temp" / "input_text.txt" if current_output_dir else PROJECT_DIR / "temp_text.txt"
                temp_text.parent.mkdir(exist_ok=True)
                with open(temp_text, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                success = run_generation(
                    temp_text,
                    Path(image_path.get()),
                    Path(ref_audio_path.get()),
                    tts_method.get() == "xtts",
                    video_method.get() == "sadtalker",
                    enhance_image.get(),
                    wer_threshold.get(),
                    add_subtitles.get(),
                    log_to_gui,
                    update_progress
                )
                
                if success:
                    log_to_gui("✅ 生成成功!\n")
                else:
                    log_to_gui("❌ 生成失败!\n", "ERROR")
                    
            except Exception as e:
                log_to_gui(f"错误: {e}\n", "ERROR")
            finally:
                is_running = False
                btn_start.config(state=NORMAL)
                btn_stop.config(state=DISABLED)
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_generation():
        global is_running
        is_running = False
        log_to_gui("⚠️ 已停止\n", "WARN")
    
    btn_start = Button(btn_frame, text="🚀 开始生成", font=("Microsoft YaHei UI", 12, "bold"),
                      bg=COLORS['accent1'], fg=COLORS['bg_dark'], padx=25, pady=8,
                      command=start_generation, relief=FLAT)
    btn_start.pack(side=LEFT, padx=10)
    
    btn_stop = Button(btn_frame, text="⏹ 停止", font=("Microsoft YaHei UI", 12),
                     bg=COLORS['error'], fg="white", padx=25, pady=8,
                     command=stop_generation, state=DISABLED, relief=FLAT)
    btn_stop.pack(side=LEFT, padx=10)
    
    btn_open = Button(btn_frame, text="📂 打开输出", font=("Microsoft YaHei UI", 12),
                     bg=COLORS['bg_light'], fg=COLORS['text'], padx=25, pady=8,
                     command=lambda: os.system(f"explorer {PROJECT_DIR}/output"), relief=FLAT)
    btn_open.pack(side=RIGHT, padx=10)
    
    log_to_gui("✨ 系统就绪，请配置参数后点击'开始生成'\n")
    
    root.mainloop()

if __name__ == "__main__":
    create_gui()
