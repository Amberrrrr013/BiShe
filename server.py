"""
Flask 后端服务
提供API接口连接前端和工作流
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import API_CONFIG, PROJECT_ROOT
from api_config import api_manager
from workflow import SpeechVideoWorkflow, WorkflowMode, VideoQuality, WorkflowConfig

app = Flask(__name__)
CORS(app)

# 全局工作流实例
workflow = None
agent_workflow_instance = None
current_text_model = None

# 模型配置映射
MODEL_CONFIGS = {
    "glm": {
        "provider": "glm",
        "api_key": "6095a09e08af4102a6b9bf2353930edc.lg7e6vBUape5NpS3",
        "model": "glm-4-flash-250414",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    "minimax": {
        "provider": "minimax",
        "api_key": "sk-cp-bMNwjtsNaMElOvU4JC9MCGW5X5RvxP6ksQIoTNUb_Pc65R8QCumrPdcEtQl9Dkdr0OKtfWC78g-KhpCPUxuwApMi1e4h9QKhVyCvLiV33H8yajDTxVJrCeM",
        "model": "MiniMax-Text-01",
        "base_url": "https://api.minimax.chat/v1",
    },
}


def get_workflow(mode="manual", model=None):
    """根据模式返回对应的工作流"""
    global workflow, agent_workflow_instance, current_text_model

    # 如果指定了模型且与当前模型不同，需要重新创建工作流
    if model and model != current_text_model:
        current_text_model = model
        workflow = None  # 强制重新创建

    if mode == "agent":
        # Agent 模式使用 AgentWorkflow
        if agent_workflow_instance is None:
            from agent_workflow import AgentWorkflow

            agent_workflow_instance = AgentWorkflow()
        return agent_workflow_instance
    else:
        # Manual/Semi-auto 模式使用 SpeechVideoWorkflow
        if workflow is None:
            # 使用当前选择的模型配置
            if current_text_model and current_text_model in MODEL_CONFIGS:
                api_config = MODEL_CONFIGS[current_text_model]
            else:
                api_config = API_CONFIG.get("text_api", {})

            full_config = API_CONFIG.copy()
            full_config["text_api"] = api_config
            config = WorkflowConfig(api_config=full_config)
            workflow = SpeechVideoWorkflow(config)
        return workflow


@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>AI 英语演讲视频生成系统 - API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #fff; }
            h1 { color: #00d9ff; }
            .endpoint { background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }
            .method { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
            .get { background: #4caf50; }
            .post { background: #2196f3; }
            code { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>AI 英语演讲视频生成系统</h1>
        <p>LangGraph-powered 英语演讲视频自动生成 API</p>
        
        <h2>可用接口</h2>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/generate</code>
            <p>启动完整的工作流生成</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/stop</code>
            <p>停止当前运行的工作流</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/status</code>
            <p>获取当前工作流状态</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/text/generate</code>
            <p>仅生成文本</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/tts/synthesize</code>
            <p>仅合成语音</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/video/generate</code>
            <p>仅生成视频</p>
        </div>
        
        <h2>前端界面</h2>
        <div style="display: flex; gap: 15px; margin-top: 10px;">
            <a href="/frontend" style="background: rgba(0,217,255,0.2); padding: 12px 24px; border-radius: 8px; color: #00d9ff; text-decoration: none; font-weight: bold;">📋 完整界面</a>
            <a href="/agent" style="background: rgba(0,255,136,0.2); padding: 12px 24px; border-radius: 8px; color: #00ff88; text-decoration: none; font-weight: bold;">🤖 AI Agent 界面</a>
        </div>
        
        <h2 style="margin-top: 30px;">AI Agent API</h2>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/agent/fullauto</code>
            <p>全自动Agent模式 - 根据自然语言需求自动生成视频</p>
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/agent/fullauto/stream</code>
            <p>全自动Agent流式接口 - 实时返回处理进度</p>
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/agent/execute</code>
            <p>根据配置执行视频生成</p>
        </div>
    </body>
    </html>
    """


@app.route("/frontend")
def frontend():
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return frontend_path.read_text(encoding="utf-8")
    return "前端文件未找到", 404


@app.route("/agent")
def agent_page():
    agent_path = Path(__file__).parent / "frontend" / "agent.html"
    if agent_path.exists():
        return agent_path.read_text(encoding="utf-8")
    return "Agent页面未找到", 404


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    启动完整的工作流生成

    请求体:
    {
        "text_mode": "user_text|ai_generate|random",
        "user_text": "...",
        "topic": "...",
        "length": 300,
        "difficulty": "easy|intermediate|advanced",
        "style": "general|business|academic|casual",
        "image_mode": "upload|camera|url|api",
        "image_source": "...",
        "image_style": {  // 当image_mode为api时的风格参数
            "gender": "female|male",
            "age": "child|teenager|young_adult|middle_aged|elderly|senior",
            "expression": "happy|sad|angry|passionate|calm|surprised",
            "background": "classroom|nature|office|park|beach|city|library|starry"
        },
        "enhance_image": true,
        "tts_method": "piper|xtts|online",
        "reference_audio": "...",
        "wer_threshold": 15,
        "video_method": "wav2lip|sadtalker|online",
        "add_subtitles": true
    }
    """
    import uuid

    config = request.json or {}

    # 处理图像路径 - 前端只发送文件名，需要转换为完整路径
    image_mode = config.get("image_mode", "upload")
    image_source = config.get("image_source", "")

    # 如果是随机模式，从图片库选择
    if image_mode == "random":
        from skills import ImageLibrary

        library_path = PROJECT_ROOT / "image_library"
        library = ImageLibrary(str(library_path))
        random_path = library.get_random_image()
        if random_path:
            config["image_source"] = random_path
            config["image_path"] = random_path
            config["image_mode"] = "upload"  # 改为upload模式，让ImageManager处理
        else:
            # 图片库为空，使用默认测试图片
            default_image = Path(r"D:\_BiShe\demo_1\test_resourse\picture_test.jpg")
            if default_image.exists():
                config["image_source"] = str(default_image)
            config["image_mode"] = "upload"
    elif image_source and not Path(image_source).exists():
        # 尝试在test_resourse目录下查找
        test_resource_path = (
            Path(r"D:\_BiShe\demo_1\test_resourse") / Path(image_source).name
        )
        if test_resource_path.exists():
            config["image_source"] = str(test_resource_path)
        else:
            # 使用默认测试图片
            default_image = Path(r"D:\_BiShe\demo_1\test_resourse\picture_test.jpg")
            if default_image.exists():
                config["image_source"] = str(default_image)

    # 处理参考音频路径 - 前端可能只发送文件名，需要转换为完整路径
    reference_audio = config.get("reference_audio", "")
    if reference_audio:
        ref_audio_path = Path(reference_audio)
        if not ref_audio_path.exists():
            # 尝试在 recordings 目录下查找
            recordings_path = (
                PROJECT_ROOT / "output" / "temp" / "recordings" / ref_audio_path.name
            )
            if recordings_path.exists():
                config["reference_audio"] = str(recordings_path)
            else:
                # 尝试其他常见路径
                alt_paths = [
                    PROJECT_ROOT / "output" / "temp" / "recordings" / reference_audio,
                    PROJECT_ROOT / "test_resourse" / reference_audio,
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        config["reference_audio"] = str(alt_path)
                        break

    def generate_events():
        wf = get_workflow(config.get('mode', 'manual'), config.get('model'))

        try:
            soundonly_mode = config.get('soundonly_mode', False)
            timestamp_str = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
            if soundonly_mode:
                timestamp_str = timestamp_str + '_soundonly'

            mode = config.get('mode', 'manual')
            if mode == 'agent':
                output_subdir = 'agent'
            else:
                output_subdir = 'non_agent'

            output_dir = PROJECT_ROOT / 'output' / output_subdir / timestamp_str
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / 'audio').mkdir(exist_ok=True)
            (output_dir / 'subtitle').mkdir(exist_ok=True)
            if not soundonly_mode:
                (output_dir / 'video').mkdir(exist_ok=True)
                (output_dir / 'image').mkdir(exist_ok=True)
            (output_dir / 'temp').mkdir(exist_ok=True)

            mode = WorkflowMode(config.get('mode', 'full_auto'))
            video_quality = VideoQuality(config.get('video_quality', 'high'))
            thread_id = str(uuid.uuid4())

            print(f"[DEBUG] Server received - tts_method: {config.get('tts_method')}, kokoro_voice: {config.get('kokoro_voice')}")

            for state in wf.graph.stream(
                {
                    'mode': mode,
                    'text_mode': config.get('text_mode', 'ai_generate'),
                    'user_text': config.get('user_text'),
                    'topic': config.get('topic'),
                    'length': config.get('length', 300),
                    'difficulty': config.get('difficulty', 'intermediate'),
                    'style': config.get('style', 'general'),
                    'image_mode': config.get('image_mode', 'upload'),
                    'image_source': config.get('image_source'),
                    'enhance_image': config.get('enhance_image', True),
                    'image_style': config.get('image_style'),
                    'image_api_provider': config.get('image_api_provider', 'minimax'),
                    'tts_method': config.get('tts_method', 'piper'),
                    'minimax_voice_id': config.get('minimax_voice_id', 'English_Graceful_Lady'),
                    'kokoro_voice': config.get('kokoro_voice', 'af_heart'),
                    'reference_audio': config.get('reference_audio'),
                    'video_method': config.get('video_method', 'sadtalker'),
                    'video_quality': video_quality,
                    'add_subtitles': config.get('add_subtitles', True),
                    'soundonly_mode': soundonly_mode,
                    'text_video_mode': config.get('text_video_mode', False),
                    'output_dir': str(output_dir),
                    'timestamp': timestamp_str,
                    'generated_text': None,
                    'audio_path': None,
                    'audio_duration': 0.0,
                    'wer_score': 0.0,
                    'image_path': None,
                    'video_path': None,
                    'final_video_path': None,
                    'current_step': 'init',
                    'error_message': None,
                    'retry_count': 0,
                    'subtitle_segments': [],
                },
                config={'configurable': {'thread_id': thread_id}},
            ):
                if not state:
                    continue

                node_name = list(state.keys())[0] if state else ''
                node_state = state.get(node_name, {}) if node_name else state

                step_map = {
                    'generate_text': 1, 'process_image': 2, 'synthesize_speech': 3,
                    'generate_video': 4, 'add_subtitles': 5, 'finalize': 6,
                }
                step_num = step_map.get(node_name, 0)

                is_skipped = False
                if soundonly_mode:
                    if node_name == 'process_image' and not node_state.get('image_path'):
                        is_skipped = True
                    elif node_name == 'generate_video':
                        is_skipped = True
                    elif node_name == 'add_subtitles':
                        is_skipped = True

                if is_skipped:
                    skip_messages = {
                        'process_image': '步骤 2 已跳过（轻量模式）',
                        'generate_video': '步骤 4 已跳过（轻量模式）',
                        'add_subtitles': '步骤 5 已跳过（轻量模式）',
                    }
                    data = {
                        'step': step_num,
                        'status': 'skipped',
                        'message': skip_messages.get(node_name, f'步骤 {step_num} 已跳过'),
                        'result': {
                            'text': node_state.get('generated_text'),
                            'image': node_state.get('image_path'),
                            'audio': node_state.get('audio_path'),
                            'video': node_state.get('video_path'),
                            'finalVideo': node_state.get('final_video_path'),
                        },
                    }
                else:
                    is_success = not node_state.get('error_message')
                    data = {
                        'step': step_num,
                        'status': 'success' if is_success else 'error',
                        'message': f"步骤 {step_num} {'完成' if is_success else '失败'}",
                        'result': {
                            'text': node_state.get('generated_text'),
                            'image': node_state.get('image_path'),
                            'audio': node_state.get('audio_path'),
                            'video': node_state.get('video_path'),
                            'finalVideo': node_state.get('final_video_path'),
                        },
                        },

                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                if not is_success:
                    break

        except Exception as e:
            data = {'step': 0, 'status': 'error', 'message': str(e)}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/stop", methods=["POST"])
def stop():
    """停止当前工作流"""
    global workflow
    workflow = None
    return jsonify({"status": "stopped"})


@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    """服务输出文件以便在前端预览"""
    from flask import send_from_directory
    import urllib.parse

    # 解码URL编码的路径
    filename = urllib.parse.unquote(filename)

    # 确保文件在output目录下（安全检查）
    safe_path = PROJECT_ROOT / "output"
    file_path = safe_path / filename

    # 检查文件是否存在且在安全路径内
    try:
        file_path = file_path.resolve()
        safe_path = safe_path.resolve()
        if not str(file_path).startswith(str(safe_path)):
            return "Forbidden", 403
        if not file_path.exists():
            return "Not found", 404
        return send_from_directory(str(safe_path), filename)
    except Exception as e:
        return str(e), 400


@app.route("/api/open_folder", methods=["POST"])
def open_folder():
    """打开文件所在位置（Windows Explorer）"""
    import subprocess
    import urllib.parse

    data = request.json or {}
    file_path = data.get("file_path", "")

    if not file_path:
        return jsonify({"success": False, "error": "No file path provided"})

    # 解码URL编码的路径
    file_path = urllib.parse.unquote(file_path)

    # 特殊目录处理
    if file_path == "image_library":
        target_path = PROJECT_ROOT / "image_library"
    else:
        # 安全检查：确保文件在项目output目录下
        try:
            file_path_obj = Path(file_path).resolve()
            safe_path = (PROJECT_ROOT / "output").resolve()
            if not str(file_path_obj).startswith(str(safe_path)):
                return jsonify(
                    {"success": False, "error": "Path outside output directory"}
                )
            target_path = file_path_obj
        except Exception:
            return jsonify({"success": False, "error": "Invalid path"})

    try:
        # Windows: 直接打开文件夹
        target_str = str(target_path.resolve())
        subprocess.Popen(f'explorer "{target_str}"', shell=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/upload_recorded_audio", methods=["POST"])
def upload_recorded_audio():
    """上传录制的音频文件"""
    import uuid
    import subprocess

    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"})

    audio_file = request.files["audio"]

    # 创建临时输出目录
    timestamp_str = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    audio_dir = PROJECT_ROOT / "output" / "temp" / "recordings"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    filename = f"recorded_audio_{timestamp_str}_{uuid.uuid4().hex[:8]}"
    raw_path = audio_dir / f"{filename}_raw.webm"
    file_path = audio_dir / f"{filename}.wav"

    try:
        # 保存原始文件
        audio_file.save(str(raw_path))

        # 使用 xtts-v2 环境的 Python 进行格式转换
        xtts_python = (
            Path(__file__).parent.parent / "xtts-v2" / "env" / "Scripts" / "python.exe"
        )
        convert_script = f'''
import sys
sys.path.insert(0, r"{Path(__file__).parent.parent / "xtts-v2" / "env" / "Lib" / "site-packages"}")
import librosa
import soundfile as sf

# 读取音频（ librosa 自动处理 webm/opus）
audio, sr = librosa.load(r"{raw_path}", sr=22050, mono=True)
# 保存为 WAV
sf.write(r"{file_path}", audio, sr)
print("Converted successfully")
'''

        result = subprocess.run(
            [str(xtts_python), "-c", convert_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # 删除原始文件
        raw_path.unlink(missing_ok=True)

        if result.returncode != 0:
            return jsonify(
                {"success": False, "error": f"音频转换失败: {result.stderr}"}
            )

        return jsonify({"success": True, "file_path": str(file_path)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    """上传用户选择的图片文件"""
    import uuid

    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided"})

    image_file = request.files["image"]

    # 创建临时输出目录
    image_dir = PROJECT_ROOT / "output" / "temp" / "uploads"
    image_dir.mkdir(parents=True, exist_ok=True)

    # 获取原始文件扩展名
    original_filename = image_file.filename
    ext = Path(original_filename).suffix if original_filename else ".jpg"
    if ext.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        ext = ".jpg"

    # 生成唯一文件名
    filename = f"user_upload_{uuid.uuid4().hex[:8]}{ext}"
    file_path = image_dir / filename

    try:
        # 保存图片
        image_file.save(str(file_path))

        return jsonify({"success": True, "file_path": str(file_path)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/upload_captured_image", methods=["POST"])
def upload_captured_image():
    """上传摄像头拍摄的图片"""
    import uuid

    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided"})

    image_file = request.files["image"]

    # 创建临时输出目录
    timestamp_str = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    image_dir = PROJECT_ROOT / "output" / "temp" / "captures"
    image_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    filename = f"camera_capture_{timestamp_str}_{uuid.uuid4().hex[:8]}.jpg"
    file_path = image_dir / filename

    try:
        # 保存图片
        image_file.save(str(file_path))

        return jsonify({"success": True, "file_path": str(file_path)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/status", methods=["GET"])
def status():
    """获取当前工作流状态"""
    try:
        from server_interactive import task_manager

        current = task_manager.get_current_task()
        active_tasks = task_manager.get_active_tasks()

        if current:
            return jsonify(
                {
                    "status": "running",
                    "task_id": current.get("task_id"),
                    "step": current.get("step", "unknown"),
                    "progress": current.get("progress", 0),
                    "message": current.get("message", ""),
                    "active_count": len(active_tasks),
                }
            )
        else:
            return jsonify(
                {"status": "idle", "message": "无进行中的任务", "active_count": 0}
            )
    except ImportError:
        # 如果交互式模块未加载，返回基本状态
        return jsonify({"status": "ready", "message": "工作流就绪"})


@app.route("/api/apis", methods=["GET"])
def get_apis():
    """获取所有API配置"""
    categories = api_manager.get_all_categories()
    result = {}
    for name, cat in categories.items():
        result[name] = {
            "category": cat.category,
            "apis": [api.to_dict() for api in cat.apis],
        }
    return jsonify(result)


@app.route("/api/apis/<category>", methods=["GET"])
def get_api_list(category):
    """获取某个分类下的所有API"""
    apis = api_manager.get_api_list(category)
    return jsonify({"category": category, "apis": apis})


@app.route("/api/apis/<category>", methods=["POST"])
def add_api(category):
    """添加新的API"""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"})

    from api_config import APIEntry

    api = APIEntry(
        name=data.get("name", "未命名"),
        provider=data.get("provider", "unknown"),
        api_key=data.get("api_key", ""),
        base_url=data.get("base_url", ""),
        **data.get("extra", {}),
    )

    api_manager.add_api(category, api)
    return jsonify({"success": True})


@app.route("/api/apis/<category>/<name>", methods=["DELETE"])
def delete_api(category, name):
    """删除API"""
    api_manager.remove_api(category, name)
    return jsonify({"success": True})


# ============= Agent 模式 API =============


@app.route("/api/agent/generate", methods=["POST"])
def agent_generate():
    """
    Agent模式生成 - 批量生成多个视频

    请求体:
    {
        "topic": "演讲主题",
        "student_count": 10,  // 批量生成数量
        "source_file": "可选，文本文件路径",
        "topics_list": ["主题1", "主题2", ...],  // 可选，指定每个学生的主题
        "image_path": "可选，指定头像路径",
        "image_library": true,  // 是否使用图片库随机选择
        "image_style": {  // AI图像风格参数（当image_source为api时使用）
            "gender": "female|male",
            "age": "child|teenager|young_adult|middle_aged|elderly|senior",
            "expression": "happy|sad|angry|passionate|calm|surprised",
            "background": "classroom|nature|office|park|beach|city|library|starry"
        },
        "tts_method": "piper|xtts|online|minimax",
        "minimax_voice_id": "English_Graceful_Lady",  // MiniMax音色ID
        "video_method": "wav2lip|sadtalker",
        "reference_audio": "可选，XTTS参考音频",
        "length": 300,  // 每个文本的目标字数
        "difficulty": "intermediate",  // 难度: elementary/middle_school/high_school/college_cet/english_major/native
        "style": "general",  // 风格: informative/motivational/persuasive/entertaining/ceremonial/keynote/demonstration/tributary/controversial/storytelling
        "model": "glm",  // AI模型: glm/minimax
        "wer_threshold": 15,  // WER阈值
        "add_subtitles": true,  // 是否添加字幕
        "soundonly_mode": false  // 是否仅生成音频
    }
    """
    import uuid
    from agent_workflow import run_single_student, run_single_student_with_progress

    config = request.json or {}

    # 如果提供了文本文件，读取主题列表
    source_file = config.get("source_file")
    if source_file and Path(source_file).exists():
        from skills import TextFromFileSkill

        skill = TextFromFileSkill()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(file_path=source_file))
        loop.close()

        if result.success:
            text = result.output.get("text", "")
            # 按行分割或按段落分割生成主题列表
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) > 1:
                config["topics_list"] = lines
                config["student_count"] = len(lines)
            else:
                config["topic"] = text[:500]  # 取前500字符作为主题
        else:
            return jsonify({"success": False, "error": f"读取文件失败: {result.error}"})

    # 如果提供了主题列表，使用主题列表
    topics_list = config.get("topics_list", [])
    student_count = config.get("student_count", len(topics_list) if topics_list else 1)

    # 如果主题中包含数量信息，自动设置学生数量
    topic = config.get("topic", "")
    if not topics_list:
        if "50" in topic or "五十" in topic:
            student_count = 50
        elif "30" in topic or "三十" in topic:
            student_count = 30
        elif "20" in topic or "二十" in topic:
            student_count = 20
        elif "10" in topic or "十" in topic:
            student_count = 10
        elif "5" in topic or "五" in topic:
            student_count = 5
        # 如果有显式的student_count，优先使用
        if config.get("student_count"):
            student_count = config["student_count"]
        config["student_count"] = student_count

        # 生成多个主题变体
        base_topic = topic.strip()
        topics_list = [f"{base_topic} - #{i + 1}" for i in range(student_count)]
        config["topics_list"] = topics_list

    def generate_events():
        try:
            completed = 0
            # 确保 topics_list 有值
            topics_list = config.get("topics_list", [])
            total = len(topics_list) if topics_list else 1
            topic_mode = config.get("topic_mode", "input")

            # 预生成随机主题列表（如果需要）
            if topic_mode == "random":
                from models.text import TextManager, SpeechRequest

                text_api_config = API_CONFIG.get("text_api", {})
                text_manager = TextManager(text_api_config)
                random_topics = []
                for i in range(student_count):
                    # 生成随机主题
                    request = SpeechRequest(
                        mode="ai_generate",
                        topic="请提供一个独特的英文演讲主题（只需返回主题词或短句，15词以内，不要解释）",
                        length=50,
                        difficulty="intermediate",
                        style="general",
                    )
                    try:
                        random_topic = text_manager.get_text(request)
                        # 清理主题文本
                        random_topic = random_topic.strip()[:100]
                        if random_topic:
                            random_topics.append(random_topic)
                        else:
                            random_topics.append(f"Topic #{i + 1}")
                    except:
                        random_topics.append(f"Topic #{i + 1}")
                topics_list = random_topics

            for i, t in enumerate(topics_list):
                student_config = config.copy()
                student_config["topic"] = t

                # 生成唯一ID
                student_id = f"student_{i + 1}_{uuid.uuid4().hex[:4]}"

                data = {
                    "type": "student_start",
                    "student_id": student_id,
                    "student_index": i + 1,
                    "total": total,
                    "topic": t,
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                # 运行单个学生工作流
                result = run_single_student(student_config)

                if result.get("status") == "complete":
                    data = {
                        "type": "student_complete",
                        "student_id": student_id,
                        "student_index": i + 1,
                        "total": total,
                        "result": result,
                        "message": f"学生 {i + 1} 处理完成",
                    }
                else:
                    data = {
                        "type": "student_error",
                        "student_id": student_id,
                        "student_index": i + 1,
                        "total": total,
                        "error": result.get("error", "未知错误"),
                        "message": f"学生 {i + 1} 处理失败: {result.get('error', '未知错误')}",
                    }

                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                completed += 1

            # 最终结果
            final_data = {
                "type": "complete",
                "total": total,
                "completed": completed,
                "message": f"全部完成! 共处理 {completed} 个学生",
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/agent/generate_stream", methods=["POST"])
def agent_generate_stream():
    """
    流式生成单个视频 - 实时返回SadTalker进度

    请求体:
    {
        "topic": "演讲主题",
        "tts_method": "piper|xtts",
        "video_method": "sadtalker|wav2lip",
        ...
    }
    """
    from agent_workflow import run_single_student_streaming

    config = request.json or {}
    topic = config.get("topic", "General Topic")
    video_method = config.get("video_method", "wav2lip")

    def generate_events():
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': f'开始生成视频: {topic}'}, ensure_ascii=False)}\n\n"

            # 运行流式工作流
            for event_type, event_data in run_single_student_streaming(config):
                if event_type == "progress":
                    yield f"data: {json.dumps({'type': 'progress', **event_data}, ensure_ascii=False)}\n\n"
                elif event_type == "sadtalker_output":
                    yield f"data: {json.dumps({'type': 'sadtalker', 'line': event_data['line'], 'is_error': event_data.get('is_error', False)}, ensure_ascii=False)}\n\n"
                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event_data.get('error', '未知错误')}, ensure_ascii=False)}\n\n"
                    return
                elif event_type == "complete":
                    yield f"data: {json.dumps({'type': 'complete', 'result': event_data, 'message': '视频生成完成'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback

            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'traceback': traceback.format_exc()}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/agent/quick_generate", methods=["POST"])
def agent_quick_generate():
    """
    快速生成单个视频（Agent模式简化版）

    请求体:
    {
        "topic": "演讲主题",
        "image_path": "可选，头像路径",
        "tts_method": "piper|xtts",
        "video_method": "wav2lip|sadtalker",
        "reference_audio": "可选，XTTS参考音频"
    }
    """
    from agent_workflow import run_single_student

    config = request.json or {}

    try:
        result = run_single_student(config)

        if result.get("status") == "complete":
            return jsonify({"success": True, "result": result})
        else:
            return jsonify({"success": False, "error": result.get("error", "生成失败")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/agent/image_library", methods=["GET"])
def agent_image_library():
    """获取图片库信息"""
    from skills import get_skills_registry

    registry = get_skills_registry()
    image_lib = registry.get_image_library()

    return jsonify(
        {"count": image_lib.get_image_count(), "path": str(image_lib.library_path)}
    )


@app.route("/api/agent/image_library/refresh", methods=["POST"])
def agent_refresh_image_library():
    """刷新图片库"""
    from skills import get_skills_registry

    registry = get_skills_registry()
    image_lib = registry.get_image_library()
    image_lib.refresh()

    return jsonify({"success": True, "count": image_lib.get_image_count()})


@app.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    """
    AI Agent聊天接口 - 基于LangGraph ReAct工具调用
    支持自然语言交互来自动生成视频

    请求体:
    {
        "message": "用户消息",
        "history": [{"role": "user"|"assistant", "content": "..."}]
    }
    """
    from ai_agent_react import create_agent

    data = request.json or {}
    user_message = data.get("message", "")
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"success": False, "error": "消息不能为空"})

    try:
        # 创建并使用ReAct Agent
        agent = create_agent()
        result = agent.chat(user_message, chat_history)

        if result.get("success"):
            return jsonify(
                {
                    "success": True,
                    "response": result.get("response", ""),
                    "config": result.get("config", {}),
                    "messages": result.get("messages", []),
                    "skill_results": result.get("skill_results", {}),
                    "is_complete": result.get("is_complete", False),
                }
            )
        else:
            return jsonify({"success": False, "error": result.get("error", "处理失败")})

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@app.route("/api/agent/fullauto", methods=["POST"])
def agent_fullauto():
    """
    全自动Agent模式 - 基于LangGraph ReAct工具调用
    根据用户自然语言需求自动生成视频

    请求体:
    {
        "message": "用户消息",
        "history": [{"role": "user"|"assistant", "content": "..."}]
    }
    """
    from ai_agent_react import create_agent

    data = request.json or {}
    user_message = data.get("message", "")
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"success": False, "error": "消息不能为空"})

    try:
        agent = create_agent()
        result = agent.chat(user_message, chat_history)

        if result.get("success"):
            return jsonify(
                {
                    "success": True,
                    "response": result.get("response", ""),
                    "config": result.get("config", {}),
                    "messages": result.get("messages", []),
                    "skill_results": result.get("skill_results", {}),
                    "is_complete": result.get("is_complete", False),
                }
            )
        else:
            return jsonify({"success": False, "error": result.get("error", "处理失败")})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/agent/fullauto/stream", methods=["POST"])
def agent_fullauto_stream():
    """
    全自动Agent模式流式接口 - 实时返回处理进度

    请求体:
    {
        "message": "用户消息",
        "history": [{"role": "user"|"assistant", "content": "..."}]
    }
    """
    from ai_agent import create_agent

    data = request.json or {}
    user_message = data.get("message", "")
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"success": False, "error": "消息不能为空"})

    def generate_events():
        try:
            agent = create_agent()

            for state_chunk in agent.chat_stream(user_message, chat_history):
                for node_name, node_state in state_chunk.items():
                    messages = node_state.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        if hasattr(last_msg, "content"):
                            yield f"data: {json.dumps({{'type': 'message', 'content': last_msg.content}}, ensure_ascii=False)}\n\n"

                    if node_state.get("current_skill_result"):
                        skill_result = node_state["current_skill_result"]
                        yield f"data: {json.dumps({{'type': 'skill_result', 'data': str(skill_result)}}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({{'type': 'complete', 'message': '处理完成'}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({{'type': 'error', 'message': str(e)}}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/agent/execute", methods=["POST"])
def agent_execute():
    """
    根据配置执行视频生成

    请求体:
    {
        "config": {
            "topic": "演讲主题",
            "length": 300,
            "difficulty": "college_cet",
            "style": "informative",
            "tts_method": "piper",
            "video_method": "sadtalker",
            ...
        }
    }
    """
    from agent_workflow import run_single_student

    data = request.json or {}
    config = data.get("config", {})

    if not config:
        return jsonify({"success": False, "error": "缺少配置参数"})

    def generate_events():
        try:
            yield f"data: {json.dumps({{'type': 'status', 'message': '开始生成视频...'}}, ensure_ascii=False)}\n\n"

            result = run_single_student(config)

            if result.get("status") == "complete":
                yield f"data: {json.dumps({{'type': 'complete', 'message': '视频生成完成', 'result': {{'text': result.get('text'), 'image': result.get('image_path'), 'audio': result.get('audio_path'), 'video': result.get('video_path'), 'quality_score': result.get('quality_score')}}}}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({{'type': 'error', 'message': result.get('error', '生成失败')}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({{'type': 'error', 'message': str(e)}}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/text/generate", methods=["POST"])
def text_generate():
    """
    仅生成文本

    请求体:
    {
        "mode": "user_text|ai_generate|random",
        "content": "..." (for user_text),
        "topic": "..." (for ai_generate),
        "length": 300,
        "difficulty": "intermediate",
        "style": "general"
    }
    """
    from models.text import TextManager, SpeechRequest

    config = request.json or {}
    mode = config.get("mode", "ai_generate")

    try:
        text_manager = TextManager(API_CONFIG.get("text_api", {}))

        request_obj = SpeechRequest(
            mode=mode,
            content=config.get("content"),
            topic=config.get("topic"),
            length=config.get("length", 300),
            difficulty=config.get("difficulty", "intermediate"),
            style=config.get("style", "general"),
        )

        text = text_manager.get_text(request_obj)

        # 保存文本
        output_path = text_manager.save_text(text, "generated_speech.txt")

        return jsonify({"success": True, "text": text, "path": output_path})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tts/synthesize", methods=["POST"])
def tts_synthesize():
    """
    仅合成语音

    请求体:
    {
        "text": "Hello world...",
        "method": "piper|xtts|online",
        "reference_audio": "..." (for xtts)
    }
    """
    from models.tts import TTSManager

    config = request.json or {}
    text = config.get("text", "")

    if not text:
        return jsonify({"success": False, "error": "缺少文本"}), 400

    try:
        tts_manager = TTSManager(API_CONFIG)

        result = tts_manager.synthesize(
            text=text,
            method=config.get("method", "piper"),
            reference_wav=config.get("reference_audio"),
        )

        return jsonify(
            {
                "success": result.success,
                "audio_path": result.audio_path,
                "duration": result.duration,
                "wer_score": result.wer_score,
                "retries": result.retries,
                "error": result.error_msg,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/image/process", methods=["POST"])
def image_process():
    """
    处理图像

    请求体:
    {
        "mode": "upload|camera|url|api",
        "source": "...",
        "enhance": true
    }
    """
    from models.image import ImageManager

    config = request.json or {}
    mode = config.get("mode", "upload")
    source = config.get("source", "")

    try:
        image_manager = ImageManager(API_CONFIG)

        result = image_manager.get_image(
            mode=mode, source=source, enhance=config.get("enhance", False)
        )

        return jsonify(
            {
                "success": result.success,
                "image_path": result.image_path,
                "width": result.width,
                "height": result.height,
                "error": result.error_msg,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/video/generate", methods=["POST"])
def video_generate():
    """
    仅生成视频

    请求体:
    {
        "image_path": "...",
        "audio_path": "...",
        "method": "wav2lip|sadtalker|online"
    }
    """
    from models.video import VideoManager

    config = request.json or {}
    image_path = config.get("image_path")
    audio_path = config.get("audio_path")

    if not image_path or not audio_path:
        return jsonify({"success": False, "error": "缺少图像或音频"}), 400

    try:
        video_manager = VideoManager(API_CONFIG)

        result = video_manager.generate_video(
            image_path=image_path,
            audio_path=audio_path,
            method=config.get("method", "sadtalker"),
        )

        return jsonify(
            {
                "success": result.success,
                "video_path": result.video_path,
                "duration": result.duration,
                "width": result.width,
                "height": result.height,
                "error": result.error_msg,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/wer/check", methods=["POST"])
def wer_check():
    """
    检查WER

    请求体:
    {
        "audio_path": "...",
        "reference_text": "..."
    }
    """
    from models.tts import WERDetector

    config = request.json or {}
    audio_path = config.get("audio_path")
    reference_text = config.get("reference_text", "")

    if not audio_path:
        return jsonify({"success": False, "error": "缺少音频路径"}), 400

    try:
        detector = WERDetector()
        result = detector.evaluate(audio_path, reference_text)

        return jsonify(
            {
                "success": True,
                "wer": result.wer,
                "wer_percentage": result.wer_percentage,
                "total_words": result.total_words,
                "errors": result.errors,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subtitle/create", methods=["POST"])
def subtitle_create():
    """
    创建字幕文件

    请求体:
    {
        "video_path": "...",
        "audio_path": "...",
        "text": "...",
        "segments": [{"start": 0, "end": 5, "text": "..."}]
    }
    """
    from models.video_editor import VideoPipeline

    config = request.json or {}
    video_path = config.get("video_path")
    audio_path = config.get("audio_path")
    text = config.get("text")
    segments = config.get("segments", [])

    if not video_path:
        return jsonify({"success": False, "error": "缺少视频路径"}), 400

    try:
        pipeline = VideoPipeline()

        output_path = pipeline.create_subtitled_video(
            video_path=video_path, audio_path=audio_path, text=text, segments=segments
        )

        return jsonify({"success": True, "output_path": output_path})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===================== 全局任务状态 =====================
import threading
import time

_task_lock = threading.Lock()
_active_tasks = {}  # task_id -> task_info
_current_task_id = None
_server_start_time = time.time()
_server_ready = False


def register_task(task_id: str, info: dict):
    """注册新任务"""
    global _current_task_id
    with _task_lock:
        info["start_time"] = time.time()
        info["last_update"] = time.time()
        info["progress"] = 0
        info["step"] = "初始化"
        _active_tasks[task_id] = info
        _current_task_id = task_id


def update_task_progress(task_id: str, **kwargs):
    """更新任务进度"""
    with _task_lock:
        if task_id in _active_tasks:
            _active_tasks[task_id].update(kwargs)
            _active_tasks[task_id]["last_update"] = time.time()


def complete_task(task_id: str, success: bool = True):
    """标记任务完成"""
    with _task_lock:
        if task_id in _active_tasks:
            _active_tasks[task_id]["completed"] = True
            _active_tasks[task_id]["success"] = success
            _active_tasks[task_id]["duration"] = (
                time.time() - _active_tasks[task_id]["start_time"]
            )
            _active_tasks[task_id]["progress"] = 100


def get_current_task():
    """获取当前任务"""
    with _task_lock:
        if _current_task_id and _current_task_id in _active_tasks:
            return _active_tasks[_current_task_id]
        return None


def get_all_tasks():
    """获取所有任务"""
    with _task_lock:
        return list(_active_tasks.values())


def get_active_tasks():
    """获取进行中的任务"""
    with _task_lock:
        return [t for t in _active_tasks.values() if not t.get("completed", False)]


# ===================== 命令行交互界面 =====================


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}分钟"
    else:
        return f"{seconds / 3600:.1f}小时"


def command_thread():
    """命令行线程 - 处理用户输入"""
    global _server_ready

    print("\n" + "=" * 50)
    print("  交互式控制台已启动")
    print("=" * 50)
    print("  输入 help 查看可用命令")
    print("=" * 50 + "\n")

    while True:
        try:
            cmd = input("> ").strip().lower()

            if not cmd:
                continue

            # 解析命令
            if cmd in ["help", "h", "?"]:
                print("\n可用命令:")
                print("  status, s    - 查看当前任务状态")
                print("  tasks, t    - 查看所有任务")
                print("  progress, p  - 查看当前进度条")
                print("  server, sv  - 查看服务器状态")
                print("  uptime, u   - 查看运行时间")
                print("  clear, cl   - 清除已完成任务")
                print("  help        - 显示此帮助")
                print("  exit, q     - 退出服务器")

            elif cmd in ["status", "s"]:
                current = get_current_task()
                if current:
                    print(f"\n当前任务: {current.get('topic', 'N/A')}")
                    print(f"步骤: {current.get('step', 'N/A')}")
                    print(f"进度: {current.get('progress', 0)}%")
                    elapsed = time.time() - current.get("start_time", time.time())
                    print(f"已运行: {format_duration(elapsed)}")
                else:
                    print("\n无进行中的任务")

            elif cmd in ["tasks", "t"]:
                all_tasks = get_all_tasks()
                active = get_active_tasks()
                print(f"\n进行中: {len(active)} 个, 总计: {len(all_tasks)} 个")
                for t in active[:5]:
                    tid = t.get("topic", "N/A")[:30]
                    print(
                        f"  • {tid} | {t.get('step', 'N/A')} | {t.get('progress', 0)}%"
                    )

            elif cmd in ["progress", "p"]:
                current = get_current_task()
                if current:
                    prog = current.get("progress", 0)
                    bar_len = 30
                    filled = int(bar_len * prog / 100)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    print(f"\n[{bar}] {prog}%")
                    print(f"步骤: {current.get('step', 'N/A')}")
                else:
                    print("\n无进行中的任务")

            elif cmd in ["server", "sv"]:
                uptime = time.time() - _server_start_time
                print(f"\n服务器状态: {'运行中' if _server_ready else '启动中'}")
                print(f"运行时间: {format_duration(uptime)}")
                print(f"活跃任务: {len(get_active_tasks())} 个")
                print(f"服务地址: http://127.0.0.1:5000")

            elif cmd in ["uptime", "u"]:
                uptime = time.time() - _server_start_time
                print(f"\n运行时间: {format_duration(uptime)}")

            elif cmd in ["clear", "cl"]:
                global _active_tasks, _current_task_id
                with _task_lock:
                    _active_tasks = {
                        k: v
                        for k, v in _active_tasks.items()
                        if not v.get("completed", False)
                    }
                    _current_task_id = None
                print("已清除已完成任务")

            elif cmd in ["exit", "quit", "q"]:
                print("\n正在停止服务器...")
                import os

                os._exit(0)
            else:
                print(f"未知命令: {cmd}")
                print("输入 help 查看可用命令")

        except EOFError:
            print("\n(输入结束，继续运行...)")
        except Exception as e:
            print(f"\n错误: {e}")




# ===================== 简单的命令行进度查看 =====================
import threading, time

_active_tasks = {}
_task_lock = threading.Lock()

def _fmt_time(s):
    if s < 60: return f"{s:.1f}秒"
    elif s < 3600: return f"{s/60:.1f}分"
    else: return f"{s/3600:.1f}小时"

def _cmd_loop():
    global _active_tasks
    while True:
        try:
            cmd = input("> ").strip().lower()
            if not cmd: continue
            if cmd in ['h','help','?']:
                print("status/s: 任务状态 | tasks/t: 所有任务 | progress/p: 进度 | server/sv: 服务器 | uptime/u: 运行时间 | exit/q: 退出")
            elif cmd in ['s','status']:
                with _task_lock:
                    if _active_tasks:
                        for k,v in _active_tasks.items():
                            print(f"{k}: {v.get('step','?')}/{v.get('progress',0)}%")
                    else: print("无进行中任务")
            elif cmd in ['t','tasks']:
                with _task_lock: print(f"{len(_active_tasks)} 个任务")
            elif cmd in ['p','progress']:
                with _task_lock:
                    for k,v in _active_tasks.items():
                        p = v.get('progress',0)
                        bar = "="*int(p/3)+"-"*((100-int(p))//3)
                        print(f"{k}: [{bar}] {p}%")
            elif cmd in ['sv','server']:
                print("服务器: 运行中 | http://127.0.0.1:5000")
            elif cmd in ['u','uptime']:
                print(f"运行时间: {_fmt_time(time.time()-1577836800)}")
            elif cmd in ['q','exit','quit']:
                import os; os._exit(0)
        except: break

if __name__ == "__main__":
    # 启动命令线程
    t = threading.Thread(target=_cmd_loop, daemon=True)
    t.start()
    
    print("=" * 50)
    print("AI 英语演讲视频生成系统")
    print("=" * 50)
    print("API: http://localhost:5000")
    print("前端: http://localhost:5000/frontend")
    print("命令: help 查看")
    print("=" * 50)
    
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
