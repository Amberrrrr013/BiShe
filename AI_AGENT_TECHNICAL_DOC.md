# AI Agent 英语演讲视频生成系统 - 技术文档

## 系统概述

本系统基于 LangGraph ReAct 模式实现 AI Agent，支持自然语言交互生成英语演讲视频。

### 核心功能
- 自然语言配置模式（先显示配置选项，再等待用户确认）
- 支持 Wav2Lip（快速）和 SadTalker（高质量）两种视频生成方式
- 实时流式进度显示（SadTalker 输出实时打印到服务器终端）
- 批量视频生成

### 技术栈
- **后端**: Flask + LangGraph + Python 3.14
- **前端**: HTML/JavaScript 单页应用
- **视频生成**: Wav2Lip, SadTalker
- **TTS**: Piper, XTTS

---

## 系统架构

```
用户请求 → /api/agent/chat (AI对话) → 返回配置选项
    ↓
用户确认 → /api/agent/generate_stream (流式生成)
    ↓
run_single_student_streaming() [agent_workflow.py]
    ↓
┌─────────────────────────────────────────────────────────────┐
│  步骤1: 文本生成 (generate_text skill)                      │
│  步骤2: 图片选择 (select_random_image skill)                │
│  步骤3: 语音合成 (synthesize_speech skill)                 │
│  步骤4: 视频生成 (generate_video skill)                     │
│         ├── Wav2Lip: 直接调用                                │
│         └── SadTalker: subprocess + 实时输出到终端           │
│  步骤5: 质量评估 (evaluate_quality skill)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心文件说明

### 1. server.py - API 服务端

**端口**: 5000

**主要端点**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/agent/chat` | POST | AI 对话，返回配置选项 |
| `/api/agent/generate_stream` | POST | 流式生成单个视频（带 SadTalker 实时输出） |
| `/api/agent/generate` | POST | 批量生成视频（返回 SSE 进度） |
| `/api/agent/quick_generate` | POST | 快速单视频生成 |
| `/api/status` | GET | 检查服务状态 |

**关键代码 - 流式生成端点**:

```python
@app.route('/api/agent/generate_stream', methods=['POST'])
def agent_generate_stream():
    """
    流式生成单个视频 - 实时返回SadTalker进度
    """
    from agent_workflow import run_single_student_streaming
    
    config = request.json or {}
    
    def generate_events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'message': f'开始生成视频: {topic}'}, ensure_ascii=False)}\n\n"
            
            for event_type, event_data in run_single_student_streaming(config):
                if event_type == 'progress':
                    yield f"data: {json.dumps({'type': 'progress', **event_data}, ensure_ascii=False)}\n\n"
                elif event_type == 'sadtalker_output':
                    yield f"data: {json.dumps({'type': 'sadtalker', 'line': event_data['line'], 'is_error': event_data.get('is_error', False)}, ensure_ascii=False)}\n\n"
                elif event_type == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'message': event_data.get('error', '未知错误')}, ensure_ascii=False)}\n\n"
                elif event_type == 'complete':
                    yield f"data: {json.dumps({'type': 'complete', 'result': event_data, 'message': '视频生成完成'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(stream_with_context(generate_events()), mimetype='text/event-stream', ...)
```

---

### 2. agent_workflow.py - 工作流核心

#### 2.1 run_single_student_streaming() - 流式工作流

**位置**: `d:\_BiShe\demo_1\agent_workflow.py` 末尾（约第 675 行起）

**功能**: 
- 支持实时进度回调
- SadTalker 视频生成时实时打印子进程输出到服务器终端

**核心流程**:

```python
def run_single_student_streaming(config: Dict[str, Any]):
    """
    运行单个学生的工作流（流式版本 - 实时返回SadTalker进度）
    """
    # 1. 生成文本
    yield ('progress', {'step': 1, 'message': '开始生成文本...', 'progress': 10})
    # ... 调用 generate_text skill ...
    yield ('progress', {'step': 1, 'message': f'文本生成完成: {word_count}词', 'progress': 30})
    
    # 2. 选择图片
    yield ('progress', {'step': 2, 'message': '开始选择图片...', 'progress': 35})
    # ... 调用 select_random_image skill ...
    yield ('progress', {'step': 2, 'message': f'随机图片: {image_path}', 'progress': 45})
    
    # 3. 合成语音
    yield ('progress', {'step': 3, 'message': '开始语音合成...', 'progress': 50})
    # ... 调用 synthesize_speech skill ...
    yield ('progress', {'step': 3, 'message': f'语音合成完成: {duration}秒', 'progress': 60})
    
    # 4. 生成视频（关键！SadTalker 实时输出）
    yield ('progress', {'step': 4, 'message': '开始视频生成...', 'progress': 65})
    
    if video_method == "sadtalker":
        # SadTalker 流式版本
        cmd = [
            str(SADTALKER_PY), str(inference_script),
            "--driven_audio", str(audio_path),
            "--source_image", str(image_path),
            "--result_dir", str(sadtalker_dir / "output"),
            "--expression_scale", "1.0",
            "--size", "512",
            "--batch_size", "2",      # 批处理大小
            "--enhancer", "None",     # 禁用面部增强
            "--fp16"                  # FP16 加速（但未真正生效！）
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, ...)
        
        def read_stdout():
            for line in process.stdout:
                print(f"[SadTalker] {line}")  # 实时打印到终端！
                output_queue.put(('stdout', line))
        
        # 启动读取线程
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)
        stdout_thread.start()
        stderr_thread.start()
        
        # 实时返回输出
        while process.poll() is None:
            try:
                msg_type, line = output_queue.get(timeout=1)
                yield ('sadtalker_output', {'line': line, 'is_error': msg_type == 'stderr'})
            except queue.Empty:
                yield ('sadtalker_output', {'line': '[SadTalker 正在生成视频...]', 'is_error': False})
```

#### 2.2 run_single_student() - 原始同步版本

**位置**: `d:\_BiShe\demo_1\agent_workflow.py` 第 499 行

**功能**: 简化版本，不返回流式进度

---

### 3. skills.py - 技能模块

**位置**: `d:\_BiShe\demo_1\skills.py`

**主要技能**:

| 技能名称 | 功能 | 关键方法 |
|----------|------|----------|
| `generate_text` | 生成英文演讲稿 | `execute(topic, length, difficulty, style)` |
| `select_random_image` | 从图片库随机选择 | `execute(prefer_new=True)` |
| `synthesize_speech` | 文本转语音 | `execute(text, method, reference_audio, ...)` |
| `generate_video` | 生成说话视频 | `execute(image_path, audio_path, method, fp16)` |
| `evaluate_quality` | 质量评估 | `execute(video_path, audio_path)` |

**关键修复 - VideoGenerationSkill**:

```python
# 原来的问题：所有视频方法都传递 fp16 参数
# result = video_manager.generate_video(..., fp16=fp16)

# 修复后：只有 SadTalker 支持 fp16
video_kwargs = {
    "image_path": image_path,
    "audio_path": audio_path,
    "method": method,
    "output_path": output_path
}
if method == "sadtalker":
    video_kwargs["fp16"] = fp16

result = video_manager.generate_video(**video_kwargs)
```

---

### 4. models/video/__init__.py - 视频生成器

**位置**: `d:\_BiShe\demo_1\models\video\__init__.py`

**类结构**:

```
VideoManager
├── Wav2LipProvider  (不支持 fp16 参数)
├── SadTalkerProvider (支持 fp16, batch_size, enhancer 参数)
└── OnlineProvider
```

**SadTalkerProvider.generate() 签名**:

```python
def generate(
    self,
    image_path: str,
    audio_path: str,
    output_path: str = None,
    expression_scale: float = 1.0,
    still_mode: bool = False,
    size: int = 512,
    batch_size: int = 2,  # 批处理大小，默认2提升速度
    video_type: str = "webp",
    fp16: bool = True  # 启用FP16混合精度加速（但未真正生效！）
) -> VideoResult:
```

**注意**: SadTalker 的 `fp16` 参数虽然被传递，但**实际未被使用**，因为 `make_animation.py` 中没有使用 `torch.cuda.amp.autocast()`。

---

### 5. frontend/index.html - 前端界面

**位置**: `d:\_BiShe\demo_1\frontend\index.html`

**关键函数 - generateSingleVideo()**:

```javascript
async function generateSingleVideo(config, progressContainer) {
    // 1. 调用流式 API
    const response = await fetch('/api/agent/generate_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic: config.topic,
            tts_method: config.tts_method || 'piper',
            video_method: config.video_method || 'wav2lip',
            // ...
        })
    });

    // 2. 实时读取 SSE 流
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.substring(6));
                
                if (data.type === 'progress') {
                    // 更新步骤进度条
                    updateStepUI(data.step, data.message, data.progress);
                } else if (data.type === 'sadtalker') {
                    // 显示 SadTalker 实时输出
                    showSadTalkerOutput(data.line);
                } else if (data.type === 'complete') {
                    // 生成完成
                }
            }
        }
    }
}
```

---

## SadTalker 优化分析

### 当前配置

| 参数 | 设置 | 效果 |
|------|------|------|
| `--batch_size` | 2 | ✅ 已生效（提升并行处理） |
| `--fp16` | 启用 | ❌ **未生效**（代码中未使用） |
| `--enhancer None` | 禁用 | ✅ 已生效（跳过面部增强） |
| `CUDA_LAUNCH_BLOCKING=1` | 启用 | ✅ 已生效（稳定CUDA） |

### FP16 未生效的原因

1. `inference.py` 第 118 行定义了 `--fp16` 参数
2. 但 `main()` 函数从未将 `args.fp16` 传递给任何模型
3. `animate_from_coeff.generate()` 调用时没有传递 fp16
4. `make_animation.py` 中没有使用 `torch.cuda.amp.autocast()`

### 真正的 FP16 加速需要修改

文件: `d:\_BiShe\sadtalker\src\facerender\make_animation.py`

需要用 `torch.cuda.amp.autocast()` 包裹前向传播代码。

---

## API 请求/响应示例

### /api/agent/generate_stream

**请求**:
```json
{
    "topic": "climate change",
    "tts_method": "piper",
    "video_method": "sadtalker",
    "length": 200
}
```

**响应 (SSE)**:
```
data: {"type": "start", "message": "开始生成视频: climate change"}

data: {"type": "progress", "step": 1, "message": "开始生成文本...", "progress": 10}
data: {"type": "progress", "step": 1, "message": "文本生成完成: 211词", "progress": 30}

data: {"type": "progress", "step": 2, "message": "随机图片: D:\\_BiShe\\demo_1\\image_library\\male_1.jpg", "progress": 45}

data: {"type": "progress", "step": 3, "message": "语音合成完成: 80.7秒", "progress": 60}

data: {"type": "progress", "step": 4, "message": "SadTalker 启动...", "progress": 68}

data: {"type": "sadtalker", "line": "[SadTalker] 开始生成视频...", "is_error": false}
data: {"type": "sadtalker", "line": "[SadTalker Error] Face Renderer::   1%| 6/1177 [00:26<1:22:41]", "is_error": true}

data: {"type": "complete", "result": {...}, "message": "视频生成完成"}
```

---

## 配置参数流向

```
前端用户选择配置
    ↓
startAgentChatGeneration() [index.html 第 2648 行]
    ↓
requestConfig = {
    topic: ...,
    tts_method: 'piper' | 'xtts' | ...,
    video_method: 'wav2lip' | 'sadtalker',
    image_gender: 'female' | 'male',
    ...
}
    ↓
/api/agent/generate_stream [server.py]
    ↓
run_single_student_streaming(config) [agent_workflow.py]
    ↓
构建 SadTalker 命令:
cmd = [
    SADTALKER_PY, inference.py,
    "--driven_audio", audio_path,
    "--source_image", image_path,
    "--result_dir", output_dir,
    "--batch_size", "2",
    "--enhancer", "None",
    "--fp16"
]
    ↓
subprocess.Popen(cmd, ...)
```

---

## 已知问题

1. **SadTalker FP16 未真正生效**: `--fp16` 参数已传递但代码未使用
2. **视频质量评分偏低**: 约为 60/100，显示"分辨率过低"

---

## 快速测试命令

```powershell
# 启动服务器
Set-Location -Path "d:\_BiShe\demo_1"
& "C:\Users\ASUS\AppData\Local\Programs\Python\Python314\python.exe" server.py

# 测试流式 API (Wav2Lip)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/agent/generate_stream" -Method Post -ContentType "application/json" -Body '{"topic":"hello","tts_method":"piper","video_method":"wav2lip","length":100}' -TimeoutSec 180

# 测试流式 API (SadTalker)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/agent/generate_stream" -Method Post -ContentType "application/json" -Body '{"topic":"hello","tts_method":"piper","video_method":"sadtalker","length":100}' -TimeoutSec 300
```

---

## 文件位置汇总

| 文件 | 路径 |
|------|------|
| 服务器入口 | `d:\_BiShe\demo_1\server.py` |
| 流式工作流 | `d:\_BiShe\demo_1\agent_workflow.py` |
| 技能模块 | `d:\_BiShe\demo_1\skills.py` |
| 视频生成器 | `d:\_BiShe\demo_1\models\video\__init__.py` |
| 前端界面 | `d:\_BiShe\demo_1\frontend\index.html` |
| SadTalker 推理 | `d:\_BiShe\sadtalker\inference.py` |
| 动画生成 | `d:\_BiShe\sadtalker\src\facerender\make_animation.py` |
| 配置 | `d:\_BiShe\demo_1\config.py` |

---

*文档生成时间: 2026年4月9日*
