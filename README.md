# AI 英语演讲视频自动生成系统

基于 LangGraph 的英语演讲视频自动生成系统，支持多种文本输入模式、TTS方法、图像处理和视频生成方案。

---

## 项目概述

本系统为毕业设计项目，可将英文演讲文本自动转换为带有人物说话头像的视频，适用于英语口语练习场景。

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

---

## 参考论文 / 资料

### 英语多模态教学相关

- [The Future of AI in Teleprompters: Enhancing Public Speaking and Broadcasting](https://www.pitchhub.com/post/the-future-of-ai-in-teleprompters-enhancing-public-speaking-and-broadcasting)
- [基于多模态学习的英语听说教学研究](https://kns.cnki.net/kcms2/article/abstract?v=Y4WXQ1XfpS7e0LbIUB_2E1mXPQ0OyWHwQWJhSFTG_ZVjpEriCNO1sOAWjDUASVHMnuSxwFkxBRJwxvHMoF8zdkjp93rikTVjxCTeOewax8DDu03AxmN95kX1ktH0AH0JUHYW_sewBAiMohTYu5hGNt3kd6dOUkDfW4KrtxHeM2cIRqC_EP2R8A==&uniplatform=NZKPT&language=CHS)
- [多模态视角下的英语教学模式创新研究](https://kns.cnki.net/kcms2/article/abstract?v=Y4WXQ1XfpS6nd0QR23ycusCiE587Ljt0KPmK9Qi6ulLZqn78FKjPF8vQLWYwrvvFFyGWvRKKRsmlr4NCfsQpFhOyUNtmeiBoELTrV5PsLWo-83-hMd9r8IXabOKjygZnPPFMsRYQxQT3yU1MVfUtsz7_j6ylwJLE-iE9PAGWFQGljJys8t36ig==&uniplatform=NZKPT&language=CHS)
- [人工智能赋能英语教学创新研究](https://kns.cnki.net/kcms2/article/abstract?v=Y4WXQ1XfpS7Q4Xo8q9SGEb18UzLRajQNOhUfH30hkJcSw7TXzI7T7gsf3FUVXZnKMoz1i4B-ltz2O05Aw4G5l9rdvsWRSt5VzUJtkR3Z-OaHW-82Lq9poRrMfbzvdiwW0Qwa55DBaHvLUMgPbGf0Gp0jmYh-JUydVZ16lfembbx-0gnSUxWuqA==&uniplatform=NZKPT&language=CHS)
- [人工智能在英语教育中的应用研究](https://kns.cnki.net/kcms2/article/abstract?v=Y4WXQ1XfpS58Rzk9xzRsWXbnkxV4i5DRKrtSHJqTRm6riZuWkgvDqP34UxGn0KB_4NNe0KVTgL86ZuXcmG5n9HGqcjkZBkJzi9EWgJogy1gGT6rsn_EIeMFUJbSuAt6xkdbMgA0iyyNry9zHv8gSuL4tr0xU2R0NGNXNq3HGNJLeSbjU84goRqsnAwHVHbWH&uniplatform=NZKPT&language=CHS)
- [面向英语教学的AI多模态交互系统设计](https://kns.cnki.net/kcms2/article/abstract?v=YNWfVykhE0YPpvD98iQoJ-cUMuIwhpVIhGcM_pVrL4LAKRgYR07tlWG6MVGQgpm01Ow5r5_-lsHarHIaBG0msop2mnwy6F8svdzVA3jKUnKIs2eo_c-FgsPD_xJ9-VgwqEQ834bkWmshwy9LJgSVVFwMkZfTtIj0P0NiJbUzNLFppN_pWfMbCQ==&uniplatform=NZKPT&language=CHS)
- [智能语音技术在英语口语教学中的应用](https://kns.cnki.net/kcms2/article/abstract?v=YNWfVykhE0b_pwlaRYpH8nrM-YMZG5AiAwYM64FwngsSLV0warSjx3KaVd2j8tgTJ4Vodwyy18hR9lL6LNLfoupKpHToqCU4VX0CRsZaYpotLciYpQ6f23gFBQniFaTm3rRgKb__gmFIqagspmZ7jckDR24z44CmB-3mWsHZDTRAegCwQpJQoQ==&uniplatform=NZKPT&language=CHS)
- [基于深度学习的英语语音识别与教学研究](https://kns.cnki.net/kcms2/article/abstract?v=YNWfVykhE0bB1q0vGtKcLAdhqf3G30MyNEv5TcA5fXR260NqO4AjUnFciuLFTJJrKU-r3AmEVaxys8JLhB64K6lrtnOVedC912KkiwXn044UguimovDDOpRVaiMHDtXuCTc814QsiBR-P58nhJL4gg5PzEjbHYwf83QUh2HxT2hL1j44w8Uemg==&uniplatform=NZKPT&language=CHS)
- [大语言模型在英语教学中的应用探索](https://kns.cnki.net/kcms2/article/abstract?v=YFFVSRMG_GF45xRT1EoH-dYRO0C0e-ibyb-Xasi1zXDWvfzaNAGUeld4-Pu8kQaEYnde_mKtYSkQ8HCdhiM-LOFu4z7ZPxFZ64WzAxvkPYwZGTBslBwrWWR4MJN9m6YQYXKGJEBctANGqQQxLNW-2jhAg3xq7zGFDJR9Q_xLk-sUJBZlwXq027ocQtghgSgc&uniplatform=NZKPT)
- [AI-Enhanced Pronunciation Training: Systematic Review](https://www.sciencedirect.com/science/article/abs/pii/S0885230825001147)
- [Multimodal Learning for English Speaking Practice](https://dl.acm.org/doi/10.1145/3482632.3483130)
- [Speech Technology for Language Learning: A Systematic Review](https://www.sciencedirect.com/science/article/pii/S0023969025001183)
- [AI in Education: English Language Teaching 4.0](https://bera-journals.onlinelibrary.wiley.com/doi/full/10.1111/bjet.13460)
- [人工智能支持下的英语多模态教学研究](https://kns.cnki.net/kcms2/article/abstract?v=9jT59j8Ji05HqjAbosqEKy7SlpCeTpSCCSgPBU1Qz5OjToYf4fJR-LW8vV4Q1B2SIVjS2TfXP_LfCm_VYp9A8BlKwjSFqScPY1wuv3BEROxVKOZFDktjg0yvIdE0MwAMOCttVx9_rVUbFU3bJo3HFuqfcdCTMRpXK4X130oygFtS2-rZjd22Yw==&uniplatform=NZKPT&language=CHS)
- [基于深度学习的多模态英语教学系统研究](https://kns.cnki.net/kcms2/article/abstract?v=9jT59j8Ji047tkNecrCsfJErLf_nhRy3Aev7bpkyF3FSG2Pl2sXjNzFqN0pcF0b-IYGlyvi-JuLpBDL_dkb8Sns1aXECUMvO7jzuLXFny2qdWE1qAB5O_BbdDWMJJUVuTH0dEawYO1yj94h7TKeuIMmJ-kKmtpfy6ga_1PjhDXoLnAqXFLtAFw==&uniplatform=NZKPT&language=CHS)
- [智能语音交互在英语口语教学中的应用研究](https://kns.cnki.net/kcms2/article/abstract?v=9jT59j8Ji05nCwKdLaP8hZaZSt-8ydbvxBzPPiK830nqOqfzukTetf9AxoJFUYJoCJb_xL0M_Fz7JROIi6iVMb11URrPeY4ebSHfsJBEZ3eGL4ECqAHt5QORGOQJ9vo_DhiEK2UXIsTS-A4PpMJMCQmshx8XQPsW6G02aAYCMzalkeKl58Aj8CoPQOHmeq7a&uniplatform=NZKPT&language=CHS)
- [多模态AI技术在英语听说教学中的应用与实践](https://kns.cnki.net/kcms2/article/abstract?v=9jT59j8Ji07W7G23cnb6XvijekQ1B3xutaXlzgBibovch_Ulgxi7GGYnacve4YcvrUBKaHK8khf-UKcVbjsnFvG5b_YwWeshzkexxUyiHhTswvSgAKKaafYLu0qpSiDt6NXT05rEIzfYRgjjctxDEFl_XVxsAmIFnisoRfn2DjBWOcQMDrGVhQ==&uniplatform=NZKPT&language=CHS)

### Agent系统搭建相关

- [LangGraph Documentation](https://blog.csdn.net/qq_42956179/article/details/143116547)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2204.07851)
- [AutoGen: Enabling Next-Gen AI Applications](https://www.sciencedirect.com/science/article/pii/S2949882125000015)
- [AgentVerse: Enhancing Multi-Agent Cooperation](https://dl.acm.org/doi/10.1145/3593013.3594011)
- [CAMEL: Communicative Agents Framework](https://dl.acm.org/doi/10.1145/3397481.3450648)
- [Role-Playing with Language Models](https://dl.acm.org/doi/10.1145/3726302.3730136)
- [Multi-Agent Collaboration in LangGraph](https://dl.acm.org/doi/10.1145/3715275.3732018)
- [Conversational AI with Multi-Agent Systems](https://dl.acm.org/doi/10.1145/3745238.3745531)
- [Building Effective AI Agents: A Survey](https://dl.acm.org/doi/10.1145/3711828)
- [OpenAI Agents SDK](https://dl.acm.org/doi/10.1145/3593013.3594011)
- [Agent-Oriented Workflow Automation](https://dl.acm.org/doi/10.1145/3746027.3755423)
- [LLM-based Autonomous Agents: A Survey](https://dl.acm.org/doi/10.1145/3721488.3721749)
- [Coze Agent Platform Documentation](https://www.coze.cn/open/docs/guides)
- [Coze Studio GitHub](https://github.com/coze-dev/coze-studio/blob/main/README.zh_CN.md)
- [Fay: Open-source Digital Human Agent](https://github.com/xszyou/Fay)
- [EMO: Emote Portrait Alive - Audio-Driven Video Generation](https://github.com/HumanAIGC/EMO)
- [Reasoning with Large Language Models](https://arxiv.org/abs/2602.11790)
- [Tool Learning with Language Models](https://arxiv.org/abs/2603.28088)
- [Multimodal Large Language Models](https://arxiv.org/abs/2601.18543)
- [Vision-Language Models for Robotics](https://arxiv.org/abs/2603.29620)
- [Large Language Model Agents: A Survey](https://arxiv.org/abs/2603.02697)
- [Understanding AI Agent Systems](https://arxiv.org/abs/2511.04570)
- [LLM Agents: Theory and Practice](https://arxiv.org/abs/2307.09368)

### 其他相关

- **语音识别 (ASR)**
  - [Whisper: OpenAI Speech Recognition](https://openai.com/index/whisper/)
  - [Whisper GitHub](https://github.com/openai/whisper)
  - [Whisper Paper](https://cdn.openai.com/papers/whisper.pdf)
  - [faster-whisper PyPI](https://pypi.org/project/faster-whisper/)
  - [Vosk Speech Recognition](https://alphacephei.com/vosk/models)
  - [Vosk API GitHub](https://github.com/alphacep/vosk-api)
  - [NVIDIA ASR Technology Guide](https://developer.nvidia.com/blog/essential-guide-to-automatic-speech-recognition-technology/)

- **唇形同步与说话人头像 (Talking Head)**
  - [SadTalker: Talking Head Generation](https://arxiv.org/abs/2210.15741)
  - [Wav2Lip: Lip Sync from Audio](https://github.com/jiwoo-jeong/wav2lip)
  - [Awesome Talking Head Synthesis](https://github.com/Kedreamix/Awesome-Talking-Head-Synthesis)
  - [MuseV: Virtual Human Video Generation](https://github.com/TMElyralab/MuseV)
  - [MuseTalk: Real-Time Talking Head](https://github.com/TMElyralab/MuseTalk)
  - [MusePose: Pose-Driven Video Generation](https://github.com/TMElyralab/MusePose)
  - [VASA-1: Microsoft's Visual-Audio Synthesis](https://www.microsoft.com/en-us/research/project/vasa-1/)
  - [EMO: Emote Portrait Alive 2](https://humanaigc.github.io/emote-portrait-alive-2/)
  - [HiAR: Human Interactive Animation](https://jacky-hate.github.io/HiAR/)
  - [Wan Video: AI Video Creation](https://create.wan.video/explore)

- **视频生成 (Video Generation)**
  - [LTX-Video: Transformer-based Video Model](https://huggingface.co/Lightricks/LTX-Video-ICLoRA-canny-13b-0.9.7)
  - [Spatial Audio Rendering for Speech Translation](https://www.microsoft.com/en-us/research/video/spatial-audio-rendering-for-speech-live-translation/)
  - [Terminal Bench Environment](https://github.com/ucsb-mlsec/terminal-bench-env)

- **技术教程与资源**
  - [知乎: 数字人多模态技术综述](https://zhuanlan.zhihu.com/p/670962982)
  - [知乎: 多模态AI数字人专题](https://zhuanlan.zhihu.com/c_1717215615826153474)
  - [知乎: AI数字人技术发展](https://zhuanlan.zhihu.com/p/1958858515323007594)
  - [腾讯云: AI数字人开发指南](https://cloud.tencent.com/developer/article/2589878)
  - [阿里云: 数字人技术解析](https://www.aliyun.com/sswb/1192813.html)
  - [腾讯云: 多模态技术应用](https://cloud.tencent.com/developer/article/2629105)
  - [Bilibili: AI技术解读](https://www.bilibili.com/opus/1165340570090995712)
  - [AutoDL平台](https://www.autodl.com/home)
  - [天池数据集: 语音数据](https://tianchi.aliyun.com/dataset/88096)
  - [天池数据集: 视频数据](https://tianchi.aliyun.com/dataset/90386)

- **开源项目**
  - [MOVA: Multimodal Open Vision Architecture](https://github.com/OpenMOSS/MOVA)
  - [aimh8 Digital Human](https://github.com/lakysir/aimh8_digital_human)
