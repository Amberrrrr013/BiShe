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
├── demo_1/                       # 主项目目录
│   ├── server.py                 # Flask API服务器（核心入口）
│   ├── workflow.py               # LangGraph工作流（手动/半自动模式）
│   ├── agent_workflow.py         # Agent工作流（批量生成模式）
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
│   └── requirements.txt          # Python依赖
│
├── piper-tts/                    # Piper TTS本地模型
├── xtts-v2/                      # XTTS V2音色克隆模型
├── kokoro-tts/                   # Kokoro TTS本地模型（新增）
├── faster-whisper/               # Faster Whisper语音识别
├── wav2lip/                      # Wav2Lip唇形同步
├── sadtalker/                    # SadTalker头部动画
└── gfpgan/                       # GFPGAN图像增强
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
| **AI生成** | 根据主题、长度、难度、风格生成 | MiniMax-M2.7 / GLM-4.6 |
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

**Kokoro 可用音色**:
- 女声: af_heart(温暖) / af_bella(清晰) / af_sarah(活泼) / af_sky(轻快) / af_nova(成熟) / af_alloy(干练) 等
- 男声: am_adam(有力) / am_michael(正式) / am_eric(自信) / am_puck(轻松) 等

**WER检测**: 使用Faster-Whisper自动检测语音与文本匹配度，WER指数未达到设定标准则重新生成，最多生成5次

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

前端界面地址: http://localhost:5000/frontend

### 3. 配置API密钥

编辑 `config.py` 中的 `API_CONFIG`：

```python
API_CONFIG = {
    "text_api": {
        "provider": "minimax",  # minimax / glm / openai
        "api_key": "你的密钥",
        "model": "MiniMax-M2.7",
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

## 参考论文

### 1. 英语演讲教学 / AI辅助英语教学

- [AI and English language teaching: Affordances and challenges](https://bera-journals.onlinelibrary.wiley.com/doi/full/10.1111/bjet.13460)
- [AI-supported English public speaking in the Chinese EFL context: Insights from self-regulated learning and positive psychology](https://www.sciencedirect.com/science/article/abs/pii/S0023969025001183)
- [AudiLens: Configurable LLM-Generated Audiences for Public Speech Practice](https://dl.acm.org/doi/10.1145/3586182.3625114)
- [English Listening Teaching Mode under Artificial Intelligence Speech Synthesis Technology](https://dl.acm.org/doi/10.1145/3615866)
- [EnglishBot: An AI-Powered Conversational System for Second Language Learning](https://dl.acm.org/doi/10.1145/3397481.3450648)
- [Large Language Models Cover for Speech Recognition Mistakes: Evaluating Conversational AI for Second Language Learners](https://dl.acm.org/doi/10.5555/3721488.3721749)
- [Learning through AI-clones: Enhancing self-perception and presentation performance](https://www.sciencedirect.com/science/article/pii/S2949882125000015)
- [MultiGen: Child-Friendly Multilingual Speech Generator with LLMs](https://dl.acm.org/doi/10.1145/3747327.3764897)
- [The Application of Computer Speech Recognition Technology in Oral English Teaching](https://dl.acm.org/doi/10.1145/3482632.3483130)
- [“讲好中国故事”视角下英语演讲课程培养跨文化能力的教学路径研究](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqtOC8aiLkhv2wGn8dRMkmCCsiSZ5juQrJK4MIalBe_jPX6-qsGdfdZci7SyDjiXI-Al2NDe4QMyBzdF7PltvMnZJI7VD5BD4UJitTiOqT46-cDp_LY6JFcIxktj5ef4PeQuD87FwyJLrwgVbh1fNviGZ-Y-H9sFnBH22soVclUOt2a0pgWQJSbz0eE0fwg54f4&uniplatform=NZKPT&captchaId=a2f85514-8a66-4fdb-a915-cbc518efcbbb)
- [大学中普及英语公众演讲课程的必要性与可行性](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqvYsReVBbvIWk7Fyxwl71a407Ibpuux6R9yDjmvWpYPMQs5dRwBI5ZtUG4LtdVpGlB7tgu20VIe7MZPaZuQRX1pBYITV1wwXP-Alv4izOA1EuZAepqlfVb-Wkbo6gYziduxgLbBkCOgR2Xe-NqxIbg6kL4OMkweE845JQYe2L0-o5Yyl-SOnud28F5b6ivnMRE&uniplatform=NZKPT&captchaId=387d7b57-f7a8-4003-843c-915ab907d6b3)
- [多模态AI技术驱动英语听说课教学评一体化模式构建](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqvKlKxCP3BP_YjaUvyJmZTFTM8xQgG-soOkE46rVirctrWTdwOYt78andvWvtHlijkVQNZxE9huqggC5h3FMYBYr7qskkj46Z9wwGkZ8URyFgquPnd_KrQn8YIhB4VvIc3rnS9bqAVw2Ki8-qbJeaSuZm8nDtkepMYmcwljRWHipBuVKRnAVK1M&uniplatform=NZKPT&captchaId=bd8f684c-b903-4cd0-8590-9d842cef7a0a)
- [人工智能（AI）辅助应用写作之优势、局限与优化——基于演讲稿教学实践的反思](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mquUyLayCPPFvdnU3HbBEiD8dvRysBvJJ9br2lhxn4V7VpXK-iezLfmg4sbc4zto59c64JYa_o4lpceASOhkeHPwTXbM_kVl0_1Y988e7MB0pkBSrkSAm0-jp-q0lrbD9Y-pXumHKrlKtPRRBJmbiBnN7jBZ6L73TNiF4HxLN1SZQ7A3EB9yICQ6HKC028ZXp70&uniplatform=NZKPT&captchaId=2fdcb683-d32e-4ef2-9f8f-447a8ea5161a)
- [人工智能多模态教学资源的生成与评价——基于AIGC在国际中文教育的应用](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqt-5xPMwbBN6kMZ4THTDb2rsYDYw8K5sILw2pe9a3TQTv8ELGfsGQRECuCGk7LXcjtncjuNfGL9_Cl5g_LnLXkqu3XFLcwTgyV0wOAkNAjS-AH3r-nvkLdyRFhfs3IDvIODGhfuSFTXIndoidjLSw5uTTjK_xCaCbXoVXcmOV_dV4Bb76H_hp6xEZVE3LTKle0&uniplatform=NZKPT&captchaId=543cc7eb-68be-4d68-a4bf-a5ae841528b0)
- [人工智能技术促进英语演讲课程教学数字化转型的创新路径研究](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqt7My1TbwDDyS_2wGjCHA1NjanLKWpapc8nrpSgj72gQgAdtj0eu8QGu7cSwGYsAfGpytiFHC1xZIVz-l3eZ3skDUToW4mqfzG607flp_CRvX_c39nz0bYE3UJoHPa4rKFJVvk-1NQx0x2sKhAIo4AGnNJcO0F3ASMKzEVR97UaVpB6zpRpBnLUaAgFETULJjY&uniplatform=NZKPT&captchaId=f445cde0-65c9-424f-9449-96a6fb13fd53)

### 2. Agent多模态应用 / Agent框架理论

- [A Survey of Multi-AI Agent Collaboration: Theories, Technologies and Applications](https://dl.acm.org/doi/10.1145/3745238.3745531)
- [AIPO: Automatic Instruction Prompt Optimization by model itself with “Gradient Ascent”](https://www.sciencedirect.com/science/article/abs/pii/S0885230825001147)
- [Beyond End-to-End Video Models: An LLM-Based Multi-Agent System for Educational Video Generation](https://arxiv.org/abs/2602.11790)
- [Cued-Agent: A Collaborative Multi-Agent System for Automatic Cued Speech Recognition](https://dl.acm.org/doi/10.1145/3746027.3755423)
- [GEMS: Agent-Native Multimodal Generation with Memory and Skills](https://arxiv.org/abs/2603.28088)
- [GenAgent: Scaling Text-to-Image Generation via Agentic Multimodal Reasoning](https://arxiv.org/abs/2601.18543)
- [More Thinking, Less Seeing? Assessing Amplified Hallucination in Multimodal Reasoning Models](https://arxiv.org/abs/2505.21523)
- [MOVA: Towards Scalable and Synchronized Video-Audio Generation](https://arxiv.org/abs/2602.08794)
- [ShareVerse: Multi-Agent Consistent Video Generation for Shared World Modeling](https://arxiv.org/abs/2603.02697)
- [TermiGen: High-Fidelity Environment and Robust Trajectory Synthesis for Terminal Agents](https://arxiv.org/abs/2602.07274)
- [Thinking with Video: Video Generation as a Promising Multimodal Reasoning Paradigm](https://arxiv.org/abs/2511.04570)
- [Unify-Agent: A Unified Multimodal Agent for World-Grounded Image Synthesis](https://arxiv.org/abs/2603.29620)
- [UniVA: Universal Video Agent towards Open-Source Next-Generation Video Generalist](https://arxiv.org/abs/2511.08521)

### 3. 文本生成语音 / 语音识别 / 语音质量评估

- [“It’s not a representation of me”: Examining Accent Bias and Digital Exclusion in Synthetic AI Voice Services](https://dl.acm.org/doi/10.1145/3715275.3732018)
- [Conformer-based Tibetan Speech Recognition Algorithm](https://dl.acm.org/doi/10.1145/3708657.3708775)
- [Good practices for evaluation of synthesized speech](https://arxiv.org/abs/2503.03250v2)
- [On the Praxes and Politics of AI Speech Emotion Recognition](https://dl.acm.org/doi/10.1145/3593013.3594011)
- [StepWrite: Adaptive Planning for Speech-Driven Text Generation](https://dl.acm.org/doi/10.1145/3746059.3747610)
- [Task-specific, personalized Automatic Speech Recognition](https://dl.acm.org/doi/10.1145/3699682.3728347)
- [基于Whisper模型的多任务学习的口语评测打分方法](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqspJ0QhLRM3G5I9D-yrtbhx7Ao22cZIG956_XVEVnVrBHKTwLZjohIjpOqClfVLe1ZrdXgV7gL34m6gIwy4Xx_ISaGF-bckn_lyjSflhFOxAy8lQHa-0Cp2V38KKRV_TgaORp3cXFfXOvoLDOZBIieFO520u68UrG8fiCpvj6j94CFBbvKZwg9u7smmMn8QB60&uniplatform=NZKPT&captchaId=d0f21d69-f163-4346-bfb8-58bbdfa76141)
- [基于Whisper模型的机载环境下的语音识别方法研究](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqs4ILDXCZFrJHFCvDKVXIh5f6aAMAFdupJDyZ_bzNNQG0REGqIeOscWs3BYKEm62CoKoS54_WX4ZImWJFMjFR3lnQQPxE0qGkgYGnSAMGBYMy6_iU1TwmxMnu6iAiD0wy1jA45Mznk6Ni_LRrZF8JzXkuiCZ8jzgQaWpQxDRX3__xOi29VlHpAkW3xtExB51GY&uniplatform=NZKPT&captchaId=5d0c1bc5-bdca-4a6d-97ff-cd6becfa8167)
- [基于机器学习与TF-IDF、Word2Vec的文本情感分析](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqtNhbDVu_q2-IcRe5CtP6U86DJoCwGw_JSNkktyiESXFeocFLIdAFFIWBqmXi836aqhoT1CKA6tBs2HKl6X2_u9OYBpmKF65uaclOLPV8-dFTZ7yQi7gOwfCqoiZnwvShICtEigNd1uVVLixmRCPD1Gm5eUD_MCMYq_8xZ6SfunN9CcSxgifHcp&uniplatform=NZKPT&captchaId=d686403c-67e4-4a09-9e8d-7b8fdea03447)

### 4. 数字人 / 唇音同步 / 视频生成

- [A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild](https://arxiv.org/abs/2008.10010)
- [Audio-driven Talking Face Generation with Stabilized Synchronization Loss](https://arxiv.org/abs/2307.09368)
- [EMO: Emote Portrait Alive -- Generating Expressive Portrait Videos with Audio2Video Diffusion Model under Weak Conditions](https://arxiv.org/abs/2402.17485)
- [HiAR: Efficient Autoregressive Long Video Generation via Hierarchical Denoising](https://arxiv.org/abs/2603.08703)
- [MuseTalk: Real-Time High-Fidelity Video Dubbing via Spatio-Temporal Sampling](https://arxiv.org/abs/2410.10122)
- [Paper2Video: Automatic Video Generation from Scientific Papers](https://arxiv.org/abs/2510.05096)
- [SadTalker: Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation](https://arxiv.org/abs/2211.12194)
- [SANA-Video: Efficient Video Generation with Block Linear Diffusion Transformer](https://arxiv.org/abs/2509.24695)
- [SyncTalk++: High-Fidelity and Efficient Synchronized Talking Heads Synthesis Using Gaussian Splatting](https://arxiv.org/abs/2506.14742)
- [VASA-1: Lifelike Audio-Driven Talking Faces Generated in Real Time](https://arxiv.org/abs/2404.10667)
- [多模态驱动情感可控的面部动画生成模型](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqtb9CdOHtHQ-r_tfBH6JZWb7iyVNIca8_IsmGjPeDMKcj8YV65VmqJ8tm7qiJmQ2TMDxdCBnkrRtav_YJujE4bfxJzLWPZIPIMi9guLJgeamrMdpyJffC4aW6_FAcxuw3mXT-P576PtNNsy7f46S-6xKaUXm-SpSHqAewuOP6KM5-JjvD0C6KKu&uniplatform=NZKPT&captchaId=73148d69-35a5-4947-b47a-4e39a40d651f)
- [融合时序建模与风格表达的2D说话人视频生成方法](https://kns.cnki.net/kcms2/article/abstract?v=y_SiIdm5mqtHA1KmyPJS-yCPgzlEP64qzwnGVc2Fkbgv1a94mh_5rM5dgZ8UpqVJlZUpDzb5VoiISvkPj_zD8JDjjGQxe1Na5z1B0E5M2eXZRvi3g4vQxIX09VKqoGakZNR8zQiwdd2vPL_0Z9DwDRnqvpD97ACRZcwxQceNAQ7XF4lsKON6ZtCAozkyFXtHiXq3JRSdvV8&uniplatform=NZKPT&captchaId=82802ddb-0785-400e-98dd-ddadc8761540)

---

## 技术教程与教学资源

- [AutoDL](https://www.autodl.com) - GPU云计算平台
- [Awesome-Talking-Head-Synthesis](https://github.com/Kedreamix/Awesome-Talking-Head-Synthesis) - 说话人脸资源库
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的AI图像/视频生成UI框架
- [ControlNet](https://github.com/lllyasviel/ControlNet) - 控制图像生成的条件扩散模型
- [Diffusers](https://github.com/huggingface/diffusers) - Hugging Face扩散模型工具库
- [Faster-whisper](https://pypi.org/project/faster-whisper/) - faster-whisper官网
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html) - FFmpeg官方文档
- [FunASR](https://github.com/modelscope/FunASR) - 阿里FunASR语音识别工具包
- [GFPGAN](https://github.com/TencentARC/GFPGAN) - 腾讯GFPGAN图像超分辨率
- [GLM API](https://bigmodel.cn/dev/api) - 智谱GLM大模型API官方文档
- [Introducing Whisper](https://openai.com/index/whisper/) - OpenAI Whisper官网
- [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) - 腾讯IP-Adapter多条件图像生成
- [LangChain Tutorials](https://python.langchain.com/docs/tutorials/) - LangChain官方教程
- [LangGraph](https://github.com/langchain-ai/langgraph) - LangChain构建Agent工作流的图框架
- [LangGraph-Course](https://github.com/microsoft/LangGraph-Course) - LangGraph官方课程
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - LangGraph官方文档
- [LibriSpeech ASR Corpus](https://www.openslr.org/12) - 1000小时英语语音识别数据集
- [LibriSpeech ASR语料库](https://tianchi.aliyun.com/dataset/88096) - 阿里云LibriSpeech中文镜像
- [MiniMax API Documentation](https://www.minimaxi.com/docs) - MiniMax API官方文档
- [MOVA](https://github.com/OpenMOSS/MOVA) - OpenMOSS同步视频音频生成开源foundation model
- [MusePose](https://github.com/TMElyralab/MusePose) - 腾讯MusePose姿态驱动图像转视频
- [MuseV](https://github.com/TMElyralab/MuseV) - 腾讯MuseV虚拟人视频生成
- [SANA-Video](https://tianchi.aliyun.com/dataset/110649) - 阿里云SANA高效视频生成
- [TED Talks Dataset](https://tianchi.aliyun.com/dataset/90386) - 阿里云TED演讲数据集(含字幕)
- [Vosk](https://alphacephei.com/vosk) - 语音识别工具
- [Wan2.1](https://github.com/Wan-Video/Wan2.1) - 视频生成开源模型
- [Whisper Tutorial](https://github.com/openai/whisper/tree/main/notebooks) - Whisper官方notebooks教程

---
