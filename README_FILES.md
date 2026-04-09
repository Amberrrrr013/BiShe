# AI 英语演讲视频生成系统 - 文件结构说明

## 一、项目概述

本项目是一个基于 LangGraph 的英语演讲视频自动生成系统，支持多种文本输入模式、TTS方法、图像处理和视频生成方案。

---

## 二、文件分类标准

| 类别 | 定义 |
|------|------|
| **关键正式文件** | 前端代码、后端代码、Agent核心业务逻辑文件 |
| **测试文件** | 文件名包含 `test`/`tests`/`spec`/`__tests__`，或位于 `test`/`tests`/`__tests__`/`spec` 目录下的文件 |
| **其他文件** | 配置、文档、脚本、生成输出等辅助文件 |

---

## 三、关键正式文件清单

### 3.1 后端核心业务文件

| 文件路径 | 作用描述 |
|----------|----------|
| `server.py` | Flask API 服务器，提供所有 REST 接口连接前端和工作流 |
| `workflow.py` | LangGraph 工作流定义（手动/半自动模式），编排文本→图像→语音→视频→字幕完整流程 |
| `agent_workflow.py` | Agent 工作流定义（批量生成模式），支持多学生并行视频生成 |
| `skills.py` | 技能系统定义，包括文本生成、图片选择、语音合成、视频生成、质量评估等 Skill |
| `config.py` | 全局配置管理，包含 API 配置、模型路径、项目根目录等 |
| `api_config.py` | API 配置管理，支持多 API 提供商动态切换 |
| `ai_agent.py` | AI Agent 实现，基于 LangGraph ReAct 模式支持自然语言交互 |
| `ai_agent_react.py` | ReAct Agent 具体实现，解析用户需求并调度各技能执行 |
| `gui_app.py` | GUI 应用程序入口（非 Web 界面） |
| `main.py` | 主程序入口，支持双击运行 |

### 3.2 模型模块文件

| 文件路径 | 作用描述 |
|----------|----------|
| `models/__init__.py` | 模型模块初始化，统一导出各子模块 |
| `models/text/__init__.py` | 文本生成模块，调用 GLM/MiniMax API 生成演讲稿 |
| `models/tts/__init__.py` | TTS 模块，支持 Piper/XTTS/MiniMax/Kokoro 等多种语音合成 |
| `models/image/__init__.py` | 图像处理模块，支持上传/摄像头/URL/AI生成/图片库 |
| `models/video/__init__.py` | 视频生成模块，调用 SadTalker/Wav2Lip 生成说话视频 |
| `models/video_editor.py` | 视频剪辑模块，使用 FFmpeg 添加字幕、合并音视频 |

### 3.3 前端文件

| 文件路径 | 作用描述 |
|----------|----------|
| `frontend/index.html` | 主界面（3标签页：AI Agent / 定制模式 / 批量模式） |
| `frontend/agent.html` | AI Agent 专用对话界面 |

---

## 四、测试文件清单

### 4.1 调试测试类文件

| 文件路径 | 作用描述 |
|----------|----------|
| `check_python.py` | 检查 Python 环境配置 |
| `check_server.py` | 检查服务器状态 |
| `debug_agent.py` | Agent 调试脚本 |
| `debug_workflow.py` | 工作流调试脚本 |
| `debug_xtts.py` | XTTS 模型调试脚本 |
| `find_python.py` | 查找 Python 路径 |
| `quick_test.py` | 快速测试脚本 |
| `run_server.py` | 服务器启动脚本 |
| `start_server.py` | 服务器启动脚本 |
| `start_correct_python.py` | 修正 Python 环境启动 |
| `run_and_capture.py` | 运行并捕获输出 |

### 4.2 分步测试脚本（step1-step8）

| 文件路径 | 作用描述 |
|----------|----------|
| `step1_piper_tts.py` | 测试 Piper TTS |
| `step2_wav2lip.py` | 测试 Wav2Lip 视频生成 |
| `step3_sadtalker.py` | 测试 SadTalker 视频生成 |
| `step4_xtts.py` | 测试 XTTS 语音合成 |
| `step5_wav2lip_xtts.py` | 测试 Wav2Lip + XTTS 组合 |
| `step6_sadtalker_xtts.py` | 测试 SadTalker + XTTS 组合 |
| `step7_wer_check.py` | 测试 WER 语音评估 |
| `step8_ffmpeg_subtitle.py` | 测试 FFmpeg 字幕烧录 |

### 4.3 单元/集成测试类文件

| 文件路径 | 作用描述 |
|----------|----------|
| `test_agent_direct.py` | Agent 直接测试 |
| `test_and_log.py` | 测试并记录日志 |
| `test_api.py` | API 接口测试 |
| `test_api_error.py` | API 错误处理测试 |
| `test_flask_api.py` | Flask API 测试 |
| `test_import.py` | 模块导入测试 |
| `test_server.py` | 服务器测试 |
| `test_split_fix.py` | 视频分割修复测试 |
| `test_text_video.py` | 文本视频测试 |
| `test_text_video_pil.py` | PIL 文本视频测试 |
| `test_tools.py` | 工具函数测试 |
| `test_wer.py` | WER 评估测试 |

---

## 五、其他文件清单

### 5.1 配置文件

| 文件路径 | 作用描述 |
|----------|----------|
| `requirements.txt` | Python 依赖包列表 |

### 5.2 文档文件

| 文件路径 | 作用描述 |
|----------|----------|
| `README.md` | 项目主说明文档 |
| `AI_AGENT_README.md` | AI Agent 功能说明 |
| `AI_AGENT_TECHNICAL_DOC.md` | AI Agent 技术文档 |
| `MEMORY.md` | 记忆系统说明 |
| `models/image/GLM_picture.md` | GLM 图像 API 使用指南 |
| `models/image/GLM_picture_api.md` | GLM 图像 API 详细文档 |
| `models/image/minimax_picture.md` | MiniMax 图像 API 使用指南 |
| `models/text/GLM_guide.md` | GLM 文本生成指南 |
| `models/tts/minimax_tts.md` | MiniMax TTS 使用指南 |
| `models/video/text_only_video_readme.md` | 纯文本视频功能说明 |
| `claude_generated_code/files/00_README.md` | Claude 生成代码说明 |

### 5.3 脚本文件

| 文件路径 | 作用描述 |
|----------|----------|
| `run.bat` | 快速启动批处理 |
| `start.bat` | 启动脚本 |
| `启动服务器.bat` | 启动 API 服务器 |
| `停止服务器.bat` | 停止 API 服务器 |
| `打开前端界面.bat` | 打开浏览器访问前端 |
| `实时监控GPU.bat` | GPU 实时监控 |
| `监控GPU进度.bat` | GPU 进度监控 |
| `GPU实时监控.bat` | GPU 监控 |
| `打包说明.txt` | 项目打包说明 |
| `claude_generated_code/files.zip` | Claude 生成代码备份压缩包 |

---

## 六、项目目录结构图

```
demo_1/
├── server.py                      ⭐ 后端API服务器
├── workflow.py                    ⭐ LangGraph工作流(手动/半自动)
├── agent_workflow.py              ⭐ Agent工作流(批量生成)
├── skills.py                      ⭐ 技能系统定义
├── config.py                      ⭐ 全局配置
├── api_config.py                  ⭐ API配置管理
├── ai_agent.py                    ⭐ AI Agent实现
├── ai_agent_react.py              ⭐ ReAct Agent实现
├── gui_app.py                     ⭐ GUI应用
├── main.py                        ⭐ 主程序入口
├── generate_videos.py             ⭐ 视频生成模块
│
├── models/                        ⭐ 模型模块
│   ├── __init__.py
│   ├── text/__init__.py           ⭐ 文本生成
│   ├── tts/__init__.py            ⭐ TTS语音合成
│   ├── image/__init__.py          ⭐ 图像处理
│   ├── video/__init__.py          ⭐ 视频生成
│   └── video_editor.py           ⭐ 视频剪辑
│
├── frontend/                     ⭐ 前端界面
│   ├── index.html                 ⭐ 主界面
│   └── agent.html                 ⭐ Agent界面
│
├── config/                        ⭐ 配置目录
│
├── test_resourse/                 📁 测试资源
│
├── output/                        📁 生成输出目录
│
├── claude_generated_code/         📁 Claude生成代码备份
│
├── requirements.txt               📄 依赖清单
├── README.md                      📄 项目说明
├── AI_AGENT_README.md             📄 Agent说明
├── AI_AGENT_TECHNICAL_DOC.md      📄 Agent技术文档
├── MEMORY.md                      📄 记忆系统说明
│
└── */*.bat                        🔧 各种批处理脚本
```

**图例**: ⭐ = 关键正式文件 | 📄 = 文档/配置 | 📁 = 目录 | 🔧 = 脚本

---

## 七、关键文件依赖关系

```
                    ┌─────────────────┐
                    │   frontend/     │
                    │  index.html     │
                    │  agent.html     │
                    └────────┬────────┘
                             │ HTTP/SSE
                    ┌────────▼────────┐
                    │   server.py     │
                    │  (Flask API)    │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐           ┌────────▼────────┐
     │   workflow.py   │           │ agent_workflow │
     │ (手动/半自动)   │           │   .py(批量)    │
     └────────┬────────┘           └────────┬────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │   skills.py    │
                    │  (技能系统)    │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐      ┌───────▼───────┐     ┌──────▼──────┐
│models/text/ │      │  models/tts/  │     │models/video/│
│ (文本生成)  │      │  (语音合成)   │     │ (视频生成)   │
└─────────────┘      └───────────────┘     └──────┬──────┘
                                                 │
                                        ┌────────▼────────┐
                                        │models/video_   │
                                        │editor.py       │
                                        │ (视频剪辑)     │
                                        └────────────────┘
```

---

## 八、快速启动

```bash
cd D:/_BiShe/demo_1
pip install -r requirements.txt
python server.py
# 浏览器打开 http://localhost:5000/frontend
```
