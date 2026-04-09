# AI 英语演讲视频自动生成系统

基于 LangGraph 的英语演讲视频自动生成系统，支持多种文本输入模式、TTS方法、图像处理和视频生成方案。

---

## 项目概述

本系统为毕业设计项目（王众），可将英文演讲文本自动转换为带有人物说话头像的视频，适用于英语口语练习场景。

**核心功能流程**:
```
文本生成 → 语音合成 → 图像获取 → 视频生成 → 字幕烧录 → 最终视频
```

---

## 项目结构

```
D:\_BiShe\
├── demo_1/                      # 主项目目录
│   ├── server.py                 # Flask API服务器（核心入口）
│   ├── workflow.py               # LangGraph工作流（手动/半自动模式）
│   ├── agent_workflow.py        # Agent工作流（批量生成模式）
│   ├── skills.py                 # 技能系统定义（7种Skill）
│   ├── config.py                 # 全局配置
│   ├── api_config.py             # API配置管理（多provider支持）
│   ├── ai_agent.py               # AI Agent实现
│   ├── ai_agent_react.py         # ReAct Agent实现
│   ├── main.py                   # 主程序入口
│   ├── gui_app.py                # GUI应用
│   ├── generate_videos.py        # 视频生成模块
│   │
│   ├── models/                   # 核心模块
│   │   ├── text/__init__.py      # 文本生成（GLM/MiniMax/本地）
│   │   ├── tts/__init__.py       # 语音合成（Piper/XTTS/MiniMax/Kokoro）
│   │   ├── image/__init__.py     # 图像处理（上传/摄像头/URL/AI生成）
│   │   ├── video/__init__.py     # 视频生成（Wav2Lip/SadTalker）
│   │   └── video_editor.py       # 视频剪辑（FFmpeg字幕烧录）
│   │
│   ├── frontend/                 # 前端界面
│   │   ├── index.html            # 主界面（AI Agent/定制模式/批量模式）
│   │   └── agent.html            # AI Agent专用对话界面
│   │
│   ├── image_library/            # 本地图片库（随机头像）
│   ├── output/                   # 生成输出目录
│   └── requirements.txt           # Python依赖
│
├── piper-tts/                   # Piper TTS本地模型
├── xtts-v2/                     # XTTS V2音色克隆模型
├── kokoro-tts/                  # Kokoro TTS本地模型（新增）
├── faster-whisper/              # Faster Whisper语音识别
├── wav2lip/                     # Wav2Lip唇形同步
├── sadtalker/                  # SadTalker头部动画
├── gfpgan/                      # GFPGAN图像增强
│
└── 王众开题报告.*               # 毕业设计开题报告
```

---

## 功能特性

### 1. 三种工作模式

| 模式 | 说明 |
|------|------|
| **AI Agent** | 自然语言交互，通过对话描述需求，系统智能解析并生成视频 |
| **定制模式** | 手动配置各项参数，生成单个视频 |
| **批量模式** | 批量生成多个视频，支持随机主题或固定主题 |

### 2. 文本生成

| 模式 | 说明 | API支持 |
|------|------|---------|
| **用户文本** | 用户直接提供完整演讲稿 | - |
| **AI生成** | 根据主题、长度、难度、风格生成 | MiniMax-Text-01 / GLM-4 / GPT-4o |
| **随机生成** | 随机生成日常口语练习文本 | - |

**难度级别**: elementary / middle_school / high_school / college_cet / english_major / native

**演讲风格**: informative / motivational / persuasive / entertaining / ceremonial / keynote / demonstration / tributary / controversial / storytelling

### 3. 语音合成（TTS）

| 方法 | 类型 | 说明 |
|------|------|------|
| **Kokoro** | 本地 | 新增！82M参数，CPU即可运行，速度极快，音质好，不可商用 |
| **Piper** | 本地 | 固定模型，快速生成 |
| **XTTS V2** | 本地 | 音色克隆，需参考音频，非商业授权 |
| **MiniMax** | 在线 | speech-2.8-hd 模型，多种音色可选 |
| **Edge TTS** | 在线 | 备用方案 |

**Kokoro 可用音色**:
- 女声: af_heart(温暖) / af_bella(清晰) / af_sarah(活泼) / af_sky(轻快) / af_nova(成熟) / af_alloy(干练) 等
- 男声: am_adam(有力) / am_michael(正式) / am_eric(自信) / am_puck(轻松) 等

**WER检测**: 使用Faster-Whisper自动检测语音与文本匹配度，不满意自动重试（最多5次）

### 4. 图像处理

| 模式 | 说明 |
|------|------|
| **上传图片** | 用户本地上传 |
| **摄像头拍摄** | 即时拍摄 |
| **URL获取** | 从网络URL下载 |
| **AI生成** | MiniMax image-01 / GLM CogView-3-Flash |
| **本地图片库** | 随机从本地图片库选择头像 |

**AI生成图像支持自定义风格参数**:
- 性别: female / male
- 年龄: child / teenager / young_adult / middle_aged / elderly / senior
- 表情: happy / sad / angry / passionate / calm / surprised
- 背景: classroom / nature / office / park / beach / city / library / starry

**GFPGAN超采样**: 可选增强图像清晰度（2倍放大）

### 5. 图生视频

| 方法 | 类型 | 说明 |
|------|------|------|
| **SadTalker** | 本地 | 高质量头部动画，支持FP16加速（1.5-1.8倍） |
| **Wav2Lip** | 本地 | 快速唇形同步 |

**SadTalker参数**:
- `--fp16`: 启用FP16混合精度加速
- `--batch_size 4`: 提升并行处理能力
- `--enhancer None`: 禁用GFPGAN（节省时间）
- `--size 512`: 输出视频尺寸

### 6. 视频剪辑

- **字幕生成**: 根据Whisper时间戳自动生成SRT字幕
- **字幕烧录**: 使用FFmpeg将字幕烧入视频底部
- **纯文本视频**: 无人物出镜的文字同步视频模式
- **仅音频模式**: 只生成音频不生成视频

---

## 快速开始

### 1. 安装依赖

```bash
cd D:\_BiShe\demo_1
pip install -r requirements.txt
```

### 2. 启动系统

```bash
cd D:\_BiShe\demo_1
python server.py
```

浏览器打开: http://localhost:5000/frontend

### 3. 配置API密钥

编辑 `config.py` 中的 `API_CONFIG`：

```python
API_CONFIG = {
    "text_api": {
        "provider": "minimax",  # minimax / glm / openai
        "api_key": "你的密钥",
        "model": "MiniMax-Text-01",
        "base_url": "https://api.minimaxi.com/v1"
    },
    "tts_api": {
        "provider": "minimax",  # minimax / kokoro / piper / xtts
        "api_key": "你的密钥",
        "voice_id": "English_Graceful_Lady"  # MiniMax音色
    },
    "image_api": {
        "provider": "minimax",  # minimax / glm
        "api_key": "你的密钥",
        "model": "image-01"
    }
}
```

---

## 前端使用说明

### AI Agent 模式
1. 点击 "AI Agent" 标签
2. 在对话框中描述需求，如："帮我制作一个关于气候变化的英语演讲视频"
3. AI自动解析需求并开始生成

### 定制模式
1. 选择文本输入方式（用户文本/AI生成/随机）
2. 配置参数（主题、长度、难度、风格）
3. 选择图像来源（上传/摄像头/AI生成/图片库）
4. 配置TTS和视频生成方式
5. 点击"开始生成"

### 批量模式
1. 选择主题模式（手动输入/随机生成）
2. 设置学生数量
3. 配置其他参数
4. 点击"开始生成"

---

## API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `POST /api/generate` | 启动完整工作流（流式） |
| `POST /api/agent/generate` | 批量生成多个视频 |
| `POST /api/agent/chat` | AI Agent聊天 |
| `POST /api/agent/fullauto` | 全自动Agent模式 |
| `POST /api/text/generate` | 仅生成文本 |
| `POST /api/tts/synthesize` | 仅合成语音 |
| `POST /api/image/process` | 处理图像 |
| `POST /api/video/generate` | 生成视频 |
| `POST /api/wer/check` | WER检测 |
| `POST /api/subtitle/create` | 创建字幕视频 |
| `GET /api/apis` | 获取所有API配置 |
| `POST /api/upload_image` | 上传图片 |
| `POST /api/upload_captured_image` | 上传摄像头图片 |
| `POST /api/upload_recorded_audio` | 上传录制的音频 |

---

## 外部模型依赖

| 模型 | 路径 | 用途 |
|------|------|------|
| Kokoro TTS | `D:\_BiShe\kokoro-tts\` | 本地快速TTS（新增） |
| Piper TTS | `D:\_BiShe\piper-tts\` | 本地固定音色TTS |
| XTTS V2 | `D:\_BiShe\xtts-v2\` | 音色克隆TTS |
| Faster Whisper | `D:\_BiShe\faster-whisper\` | 语音识别/WER检测 |
| Wav2Lip | `D:\_BiShe\wav2lip\` | 唇形同步视频 |
| SadTalker | `D:\_BiShe\sadtalker\` | 头部动画视频 |
| GFPGAN | `D:\_BiShe\gfpgan\` | 图像超分辨率增强 |

每个模型目录包含独立的虚拟环境 (`env/Scripts/python.exe`)

---

## 注意事项

1. **API密钥**: 在线功能需要配置相应API密钥
   - MiniMax: https://www.minimaxi.com
   - GLM: https://bigmodel.cn

2. **FFmpeg**: 视频剪辑功能需要安装ffmpeg并添加到PATH

3. **GPU**: 建议使用NVIDIA GPU以加速SadTalker/Wav2Lip/XTTS推理

4. **图片库**: `image_library/` 文件夹可存放任意数量头像图片

5. **TTS选择建议**:
   - 默认使用 Kokoro（快速、音质好、CPU可运行）
   - 需要音色克隆时使用 XTTS V2
   - 在线TTS使用 MiniMax

---

## 项目特点

- **多模式支持**: 手动、半自动、Agent三种工作模式
- **多TTS方案**: Kokoro(新增)/Piper/XTTS/MiniMax/Edge
- **批量生成**: 支持一次性生成多个视频
- **模块化设计**: 文本、TTS、图像、视频处理分离
- **LangGraph工作流**: 基于图的状态机，确保流程可靠
- **流式输出**: SSE实时返回处理进度

---

## 文件分类

| 类别 | 文件 |
|------|------|
| **后端核心** | server.py / workflow.py / agent_workflow.py / skills.py / config.py / api_config.py |
| **模型模块** | models/text/__init__.py / models/tts/__init__.py / models/image/__init__.py / models/video/__init__.py / models/video_editor.py |
| **Agent** | ai_agent.py / ai_agent_react.py |
| **前端** | frontend/index.html / frontend/agent.html |
| **测试文件** | step*.py / test*.py / debug*.py / check*.py（共25个） |
| **文档** | README.md / AI_AGENT_README.md / AI_AGENT_TECHNICAL_DOC.md / kokoro_README.md 等 |

---

## 许可证

MIT License
