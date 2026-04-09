# 毕设各模块环境总览
# 基于AI Agent技术的英语演讲示范视频生成系统

## 目录结构
```
D:\_BiShe\
├── faster-whisper\     # 语音转文字（ASR）
│   └── env\
├── piper-tts\          # 轻量英文TTS（备用）
│   └── env\
├── xtts-v2\            # 高质量音色克隆TTS（主用）
│   └── env\
├── wav2lip\            # 唇形同步视频生成
│   └── env\
├── gfpgan\             # 人脸超分辨率修复
│   └── env\
└── sadtalker\          # 带头部运动的说话人视频生成
    └── env\
```

## 各模块说明

| 文件 | 模块 | 环境目录 | GPU | 用途 |
|------|------|----------|-----|------|
| 01_faster_whisper_test.py | faster-whisper | faster-whisper\env | ✅ | ASR转录/WER检测 |
| 02_piper_tts_test.py | piper-tts | piper-tts\env | ❌ | 备用轻量TTS |
| 03_xtts_v2_test.py | XTTS-v2 | xtts-v2\env | ✅ | 主用TTS，支持音色克隆 |
| 04_wav2lip_test.py | Wav2Lip | wav2lip\env | ✅ | 唇形同步，速度快 |
| 05_gfpgan_test.py | GFPGAN | gfpgan\env | ✅ | 人脸修复，用于预处理图片 |
| 06_sadtalker_test.py | SadTalker | sadtalker\env | ✅ | 带头部运动，画质较好 |

## 重要版本记录（避免踩坑）

### xtts-v2 环境
- torch==2.5.1+cu121
- transformers==4.40.0  ← 必须降级，新版缺少 BeamSearchScorer
- TTS==0.22.0

### wav2lip 环境
- numpy==1.23.5
- librosa==0.9.2  ← 必须降级，新版 API 不兼容
- opencv-python==4.11.0.86

### gfpgan 环境
- torch==2.1.2+cu121
- torchvision==0.16.2  ← 必须降级，新版缺少 functional_tensor
- numpy==1.26.4  ← 必须锁定，每次装新包后需重新执行

### sadtalker 环境
- torch==2.1.2+cu121
- torchvision==0.16.2  ← 同 gfpgan
- numpy==1.23.4（requirements.txt 指定）

## Agent 流程（LangGraph）

```
用户输入主题
    ↓
DeepSeek API 生成演讲稿
    ↓
质量检测（长度/结构）→ 不合格回到上一步（最多3次）
    ↓
XTTS-v2 生成语音（xtts-v2\env）
    ↓
faster-whisper ASR检测WER（faster-whisper\env）→ 不合格重新生成
    ↓
GFPGAN 预处理人脸图片（gfpgan\env）
    ↓
Wav2Lip 或 SadTalker 生成视频（wav2lip\env 或 sadtalker\env）
    ↓
ffmpeg 叠加字幕 + 章节时间轴
    ↓
输出成品视频
```

## 注意事项
- 各模块使用独立虚拟环境，不要混用
- 各模块在 Agent 中通过 subprocess 调用，指定各自的 python.exe 路径
- numpy 版本是最常见的冲突来源，每次装新包后检查版本
- 模型文件较大，不要重复下载，统一缓存位置：
  - HuggingFace 模型：C:\Users\ASUS\.cache\huggingface\
  - XTTS-v2 模型：C:\Users\ASUS\AppData\Local\tts\
