"""
LangGraph 工作流整合模块
整合文本生成、TTS、图像处理、视频生成、视频剪辑为完整流水线
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import API_CONFIG, OUTPUT_DIR

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from typing_extensions import TypedDict
except ImportError:
    print("请安装langgraph: pip install langgraph")
    sys.exit(1)


class WorkflowMode(Enum):
    """工作流模式"""
    FULL_AUTO = "full_auto"      # 全自动模式
    SEMI_AUTO = "semi_auto"     # 半自动模式
    MANUAL = "manual"            # 手动模式


class VideoQuality(Enum):
    """视频质量选项"""
    FAST = "fast"               # 快速模式 (Wav2Lip)
    HIGH = "high"               # 高质量模式 (SadTalker)


@dataclass
class WorkflowState(TypedDict):
    """工作流状态"""
    # 输入参数
    mode: WorkflowMode
    text_mode: str                    # "user_text", "ai_generate", "random"
    
    # 图像参数
    image_mode: str                    # "camera", "upload", "url", "api"
    image_source: Optional[str] = None
    enhance_image: bool = False
    image_style: Optional[Dict[str, str]] = None  # AI图像风格参数
    
    # TTS参数
    tts_method: str = "piper"          # "piper", "xtts", "online"
    minimax_voice_id: Optional[str] = "English_Graceful_Lady"
    kokoro_voice: Optional[str] = "af_heart"
    reference_audio: Optional[str] = None
    
    # 视频参数
    video_method: str = "sadtalker"   # "wav2lip", "sadtalker", "online"
    video_quality: VideoQuality = VideoQuality.HIGH
    
    # 文本参数 (这些是可选的)
    user_text: Optional[str] = None
    topic: Optional[str] = None
    length: Optional[int] = None
    difficulty: Optional[str] = None
    style: Optional[str] = None
    
    # 处理结果
    generated_text: Optional[str] = None
    audio_path: Optional[str] = None
    audio_duration: float = 0.0
    wer_score: float = 0.0
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    final_video_path: Optional[str] = None
    
    # 状态信息
    current_step: str = "init"
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # 字幕相关
    add_subtitles: bool = True
    subtitle_segments: List[Dict[str, Any]] = field(default_factory=list)
    
    # 仅生成音频模式
    soundonly_mode: bool = False
    text_video_mode: bool = False
    
    # 输出目录 (时间戳目录)
    output_dir: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class WorkflowConfig:
    """工作流配置"""
    api_config: Dict[str, Any] = field(default_factory=lambda: API_CONFIG)
    output_dir: Path = OUTPUT_DIR
    wer_threshold: float = 0.15
    max_retries: int = 5
    add_subtitles: bool = True


class SpeechVideoWorkflow:
    """英语演讲视频生成工作流"""
    
    def __init__(self, config: WorkflowConfig = None):
        self.config = config or WorkflowConfig()
        
        # 初始化各个管理器
        from models.text import TextManager
        from models.tts import TTSManager
        from models.image import ImageManager
        from models.video import VideoManager
        from models.video_editor import VideoPipeline
        
        api_config = self.config.api_config
        self.text_manager = TextManager(api_config.get('text_api', {}))
        self.tts_manager = TTSManager(api_config.get('tts_api', {}))
        self.image_manager = ImageManager(api_config.get('image_api', {}))
        self.video_manager = VideoManager(api_config.get('video_api', {}))
        self.video_pipeline = VideoPipeline()
        
        # 初始化检查点存储器
        self.checkpointer = MemorySaver()
        
        # 构建图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("generate_text", self._generate_text_node)
        workflow.add_node("process_image", self._process_image_node)
        workflow.add_node("synthesize_speech", self._synthesize_speech_node)
        workflow.add_node("generate_video", self._generate_video_node)
        workflow.add_node("add_subtitles", self._add_subtitles_node)
        workflow.add_node("finalize", self._finalize_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # 设置入口点
        workflow.set_entry_point("generate_text")
        
        # 添加条件边以支持仅生成音频模式
        def should_skip_video(state: WorkflowState) -> str:
            """决定语音合成后的下一个节点"""
            if state.get("soundonly_mode", False):
                # 仅生成音频模式
                if state.get("text_video_mode", False):
                    return "add_subtitles"  # 纯文本视频模式，跳过视频，直接生成字幕
                return "finalize"  # 纯音频模式
            return "generate_video"
        
        def should_skip_image(state: WorkflowState) -> str:
            """决定文本生成后的下一个节点"""
            if state.get("text_video_mode", False):
                return "synthesize_speech"  # 纯文本视频模式，跳过图片处理
            return "process_image"
        
        # 添加边
        # 条件边：根据text_video_mode决定是否跳过图片处理
        workflow.add_conditional_edges(
            "generate_text",
            should_skip_image,
            {
                "process_image": "process_image",
                "synthesize_speech": "synthesize_speech",
            }
        )
        workflow.add_edge("process_image", "synthesize_speech")
        
        # 条件边：根据soundonly_mode和text_video_mode决定后续步骤
        workflow.add_conditional_edges(
            "synthesize_speech",
            should_skip_video,
            {
                "finalize": "finalize",  # 仅生成音频
                "add_subtitles": "add_subtitles",  # 纯文本视频模式
                "generate_video": "generate_video",  # 生成视频
            }
        )
        workflow.add_edge("generate_video", "add_subtitles")
        workflow.add_edge("add_subtitles", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _generate_text_node(self, state: WorkflowState) -> WorkflowState:
        """生成文本节点"""
        state["current_step"] = "generate_text"
        
        try:
            from models.text import SpeechRequest
            
            request = SpeechRequest(
                mode=state["text_mode"],
                content=state.get("user_text"),
                topic=state.get("topic"),
                length=state.get("length", 300),
                difficulty=state.get("difficulty", "intermediate"),
                style=state.get("style", "general")
            )
            
            text = self.text_manager.get_text(request)
            state["generated_text"] = text
            
            # 保存文本
            text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
            output_dir = Path(state.get('output_dir', self.config.output_dir))
            text_path = output_dir / "text" / f"speech_{text_hash}.txt"
            text_path.parent.mkdir(parents=True, exist_ok=True)
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            print(f"[Step 1/5] 文本生成完成: {len(text)} 字符")
            
        except Exception as e:
            state["error_message"] = f"文本生成失败: {e}"
        
        return state
    
    def _process_image_node(self, state: WorkflowState) -> WorkflowState:
        """处理图像节点"""
        state["current_step"] = "process_image"
        
        # 仅生成音频模式跳过图像处理
        if state.get("soundonly_mode", False):
            print("[Step 2/5] 图像处理已跳过（仅生成音频）")
            return state
        
        try:
            # 确定输出路径 - 使用时间戳目录
            output_dir = Path(state.get('output_dir', self.config.output_dir))
            image_subdir = output_dir / "image"
            image_subdir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            import uuid
            image_filename = f"source_{uuid.uuid4().hex[:8]}.jpg"
            image_output_path = str(image_subdir / image_filename)
            
            # 获取图片风格参数
            image_style = state.get("image_style") or {}
            # 获取API提供商
            api_provider = state.get("image_api_provider", "minimax")
            
            result = self.image_manager.get_image(
                mode=state["image_mode"],
                source=state.get("image_source", ""),
                output_path=image_output_path,
                enhance=state.get("enhance_image", False),
                api_provider=api_provider,
                **image_style
            )
            
            if result.success:
                state["image_path"] = result.image_path
                print(f"[Step 2/5] 图像处理完成: {result.width}x{result.height}")
            else:
                state["error_message"] = f"图像处理失败: {result.error_msg}"
                
        except Exception as e:
            state["error_message"] = f"图像处理失败: {e}"
        
        return state
    
    def _synthesize_speech_node(self, state: WorkflowState) -> WorkflowState:
        """合成语音节点"""
        state["current_step"] = "synthesize_speech"
        
        try:
            text = state.get("generated_text")
            if not text:
                state["error_message"] = "没有可用的文本"
                return state
            
            # 确定输出路径 - 使用时间戳目录
            output_dir = Path(state.get('output_dir', self.config.output_dir))
            audio_subdir = output_dir / "audio"
            audio_subdir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            import uuid
            audio_filename = f"tts_{state['tts_method']}_{uuid.uuid4().hex[:8]}.wav"
            audio_output_path = str(audio_subdir / audio_filename)
            
            # 如果使用MiniMax TTS，设置音色ID
            if state["tts_method"] == "minimax":
                minimax_voice_id = state.get("minimax_voice_id", "English_Graceful_Lady")
                print(f"[DEBUG] MiniMax TTS: setting voice_id to '{minimax_voice_id}'")
                # 直接设置 online_provider 的 api_config
                online_provider = self.tts_manager.providers.get("minimax")
                if online_provider:
                    online_provider.api_config["provider"] = "minimax"
                    online_provider.api_config["voice_id"] = minimax_voice_id
                    print(f"[DEBUG] OnlineProvider api_config set: {online_provider.api_config}")
            
            # 如果使用Kokoro TTS，设置音色
            elif state["tts_method"] == "kokoro":
                kokoro_voice = state.get("kokoro_voice", "af_heart")
                print(f"[DEBUG] Kokoro TTS: tts_method={state['tts_method']}, kokoro_voice={kokoro_voice}")
                # 直接设置 online_provider 的 api_config
                online_provider = self.tts_manager.providers.get("kokoro")
                if online_provider:
                    online_provider.api_config["provider"] = "kokoro"
                    online_provider.api_config["voice"] = kokoro_voice
                    print(f"[DEBUG] OnlineProvider api_config set: {online_provider.api_config}")
            
            tts_result = self.tts_manager.synthesize(
                text=text,
                method=state["tts_method"],
                reference_wav=state.get("reference_audio"),
                output_filename=audio_output_path
            )
            
            state["audio_path"] = tts_result.audio_path
            state["audio_duration"] = tts_result.duration
            state["wer_score"] = tts_result.wer_score
            state["retry_count"] = tts_result.retries
            
            if tts_result.success:
                print(f"[Step 3/5] 语音合成完成: WER={tts_result.wer_score:.2%}, 时长={tts_result.duration:.1f}s")
            else:
                state["error_message"] = f"语音合成失败: {tts_result.error_msg}"
                
        except Exception as e:
            state["error_message"] = f"语音合成失败: {e}"
        
        return state
    
    def _check_tts_success(self, state: WorkflowState) -> str:
        """检查TTS是否成功"""
        if state.get("error_message"):
            return "failed"
        
        wer_score = state.get("wer_score", 1.0)
        if wer_score > self.config.wer_threshold:
            if state.get("retry_count", 0) < self.config.max_retries:
                return "retry"
        
        return "success"
    
    def _generate_video_node(self, state: WorkflowState) -> WorkflowState:
        """生成视频节点"""
        state["current_step"] = "generate_video"
        
        try:
            image_path = state.get("image_path")
            audio_path = state.get("audio_path")
            
            if not image_path or not audio_path:
                state["error_message"] = "缺少图像或音频"
                return state
            
            # 确定输出路径 - 使用时间戳目录
            output_dir = Path(state.get('output_dir', self.config.output_dir))
            video_subdir = output_dir / "video"
            video_subdir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            import uuid
            video_filename = f"{state['video_method']}_{uuid.uuid4().hex[:8]}.mp4"
            video_output_path = str(video_subdir / video_filename)
            
            video_result = self.video_manager.generate_video(
                image_path=image_path,
                audio_path=audio_path,
                method=state["video_method"],
                output_path=video_output_path
            )
            
            if video_result.success:
                state["video_path"] = video_result.video_path
                print(f"[Step 4/5] 视频生成完成: {video_result.width}x{video_result.height}, {video_result.duration:.1f}s")
            else:
                state["error_message"] = f"视频生成失败: {video_result.error_msg}"
                
        except Exception as e:
            state["error_message"] = f"视频生成失败: {e}"
        
        return state
    
    def _add_subtitles_node(self, state: WorkflowState) -> WorkflowState:
        """添加字幕节点"""
        state["current_step"] = "add_subtitles"
        
        try:
            video_path = state.get("video_path")
            audio_path = state.get("audio_path")
            text = state.get("generated_text")
            is_text_video = state.get("text_video_mode", False)
            
            # 检查是否仅生成音频模式（没有视频）
            is_soundonly = state.get("soundonly_mode", False)
            
            # 仅生成音频模式不需要添加字幕
            if is_soundonly and not is_text_video:
                state["final_video_path"] = audio_path
                print("[Step 4/4] 仅音频模式完成")
                return state
            
            # 获取字幕时间戳
            try:
                _, segments = self.tts_manager.wer_detector.transcribe(audio_path)
                state["subtitle_segments"] = [
                    {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                    for s in segments
                ]
            except Exception as e:
                print(f"获取字幕时间戳失败: {e}")
                state["subtitle_segments"] = []
            
            # 生成字幕视频
            output_dir = Path(state.get('output_dir', self.config.output_dir))
            (output_dir / "final").mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "final" / "final_output.mp4")
            
            if is_text_video:
                # 纯文本视频模式（无人物出镜）
                print(f"[Step 4/4] 使用纯文本视频模式（文字同步）")
                final_path = self.video_pipeline.create_text_only_video(
                    audio_path=audio_path,
                    text=text,
                    segments=state["subtitle_segments"],
                    output_path=output_path
                )
            else:
                # 底部字幕模式（人物出镜）
                print(f"[Step 4/4] 使用底部字幕模式")
                final_path = self.video_pipeline.create_subtitled_video(
                    video_path=video_path,
                    audio_path=audio_path,
                    text=text,
                    segments=state["subtitle_segments"],
                    output_path=output_path
                )
            
            state["final_video_path"] = final_path
            print(f"[Step 4/4] 字幕添加完成")
            
        except Exception as e:
            state["error_message"] = f"添加字幕失败: {e}"
            state["final_video_path"] = state.get("video_path") or state.get("audio_path")  # 降级
            
        return state
    
    def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """最终化节点"""
        state["current_step"] = "finalize"
        
        # 仅生成音频模式：最终输出是音频或文本视频
        if state.get("soundonly_mode", False):
            final_path = state.get("final_video_path") or state.get("audio_path")
            # 设置final_video_path为audio_path以便前端获取
            state["final_video_path"] = final_path
            print("\n" + "="*50)
            print("工作流完成（仅生成音频）!")
            print(f"最终输出: {final_path}")
            print("="*50)
        else:
            final_path = state.get("final_video_path") or state.get("video_path")
            print("\n" + "="*50)
            print("工作流完成!")
            print(f"最终输出: {final_path}")
            print("="*50)
        
        return state
    
    def _handle_error_node(self, state: WorkflowState) -> WorkflowState:
        """错误处理节点"""
        state["current_step"] = "handle_error"
        print(f"\n错误: {state.get('error_message')}")
        return state
    
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            Dict: 最终状态
        """
        # 转换模式
        mode = config.get("mode", WorkflowMode.FULL_AUTO)
        if isinstance(mode, str):
            mode = WorkflowMode(mode)
        
        video_quality = config.get("video_quality", VideoQuality.HIGH)
        if isinstance(video_quality, str):
            video_quality = VideoQuality(video_quality)
        
        # 初始化状态
        initial_state: WorkflowState = {
            "mode": mode,
            "text_mode": config.get("text_mode", "ai_generate"),
            "user_text": config.get("user_text"),
            "topic": config.get("topic"),
            "length": config.get("length", 300),
            "difficulty": config.get("difficulty", "intermediate"),
            "style": config.get("style", "general"),
            "image_mode": config.get("image_mode", "upload"),
            "image_source": config.get("image_source"),
            "enhance_image": config.get("enhance_image", False),
            "tts_method": config.get("tts_method", "piper"),
            "reference_audio": config.get("reference_audio"),
            "video_method": config.get("video_method", "sadtalker"),
            "video_quality": video_quality,
            "add_subtitles": config.get("add_subtitles", True),
            "generated_text": None,
            "audio_path": None,
            "audio_duration": 0.0,
            "wer_score": 0.0,
            "image_path": None,
            "video_path": None,
            "final_video_path": None,
            "current_step": "init",
            "error_message": None,
            "retry_count": 0,
            "subtitle_segments": []
        }
        
        # 运行工作流
        result = self.graph.invoke(initial_state)
        
        return result
    
    def run_step_by_step(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        逐步运行工作流
        
        Returns:
            List[Dict]: 每个步骤的状态列表
        """
        mode = config.get("mode", WorkflowMode.FULL_AUTO)
        if isinstance(mode, str):
            mode = WorkflowMode(mode)
        
        initial_state: WorkflowState = {
            "mode": mode,
            "text_mode": config.get("text_mode", "ai_generate"),
            "user_text": config.get("user_text"),
            "topic": config.get("topic"),
            "length": config.get("length", 300),
            "difficulty": config.get("difficulty", "intermediate"),
            "style": config.get("style", "general"),
            "image_mode": config.get("image_mode", "upload"),
            "image_source": config.get("image_source"),
            "enhance_image": config.get("enhance_image", False),
            "tts_method": config.get("tts_method", "piper"),
            "reference_audio": config.get("reference_audio"),
            "video_method": config.get("video_method", "sadtalker"),
            "video_quality": config.get("video_quality", VideoQuality.HIGH),
            "add_subtitles": config.get("add_subtitles", True),
            "generated_text": None,
            "audio_path": None,
            "audio_duration": 0.0,
            "wer_score": 0.0,
            "image_path": None,
            "video_path": None,
            "final_video_path": None,
            "current_step": "init",
            "error_message": None,
            "retry_count": 0,
            "subtitle_segments": []
        }
        
        states = []
        
        # 创建新的图实例用于逐步执行
        app = self.graph
        
        # 使用 interrupt 可以在某些节点暂停
        for state in app.stream(initial_state):
            states.append(state)
        
        return states


class SemiAutoWorkflow(SpeechVideoWorkflow):
    """半自动工作流 - 允许在每步完成后进行人工确认和调整"""
    
    def run_with_approval(
        self,
        config: Dict[str, Any],
        approval_callback=None
    ) -> Dict[str, Any]:
        """
        带审批的工作流
        
        Args:
            config: 工作流配置
            approval_callback: 每步完成后的回调函数，接收当前状态，返回是否继续
        """
        mode = config.get("mode", WorkflowMode.SEMI_AUTO)
        if isinstance(mode, str):
            mode = WorkflowMode(mode)
        
        # 第一步：文本生成
        state = self._run_text_generation(config)
        if approval_callback:
            if not approval_callback(state, "text"):
                return state
        
        # 第二步：图像处理
        state = self._run_image_processing(state, config)
        if approval_callback:
            if not approval_callback(state, "image"):
                return state
        
        # 第三步：语音合成
        state = self._run_speech_synthesis(state)
        if approval_callback:
            if not approval_callback(state, "speech"):
                return state
        
        # 第四步：视频生成
        state = self._run_video_generation(state)
        if approval_callback:
            if not approval_callback(state, "video"):
                return state
        
        # 第五步：字幕添加
        state = self._run_subtitle_addition(state)
        
        return state
    
    def _run_text_generation(self, config: Dict[str, Any]) -> WorkflowState:
        """运行文本生成步骤"""
        from models.text import SpeechRequest
        
        state = WorkflowState(
            mode=WorkflowMode.SEMI_AUTO,
            text_mode=config.get("text_mode", "ai_generate"),
            user_text=config.get("user_text"),
            topic=config.get("topic"),
            length=config.get("length", 300),
            difficulty=config.get("difficulty", "intermediate"),
            style=config.get("style", "general"),
            image_mode=config.get("image_mode", "upload"),
            image_source=config.get("image_source"),
            enhance_image=config.get("enhance_image", False),
            image_style=config.get("image_style"),
            tts_method=config.get("tts_method", "piper"),
            reference_audio=config.get("reference_audio"),
            video_method=config.get("video_method", "sadtalker"),
            video_quality=VideoQuality(config.get("video_quality", "high")),
            add_subtitles=config.get("add_subtitles", True)
        )
        
        return self._generate_text_node(state)
    
    def _run_image_processing(self, state: WorkflowState, config: Dict) -> WorkflowState:
        """运行图像处理步骤"""
        return self._process_image_node(state)
    
    def _run_speech_synthesis(self, state: WorkflowState) -> WorkflowState:
        """运行语音合成步骤"""
        return self._synthesize_speech_node(state)
    
    def _run_video_generation(self, state: WorkflowState) -> WorkflowState:
        """运行视频生成步骤"""
        return self._generate_video_node(state)
    
    def _run_subtitle_addition(self, state: WorkflowState) -> WorkflowState:
        """运行字幕添加步骤"""
        return self._add_subtitles_node(state)


# 便捷函数
def create_full_auto_workflow(config: WorkflowConfig = None) -> SpeechVideoWorkflow:
    """创建全自动工作流"""
    return SpeechVideoWorkflow(config)


def create_semi_auto_workflow(config: WorkflowConfig = None) -> SemiAutoWorkflow:
    """创建半自动工作流"""
    return SemiAutoWorkflow(config)


# 导出
__all__ = [
    "SpeechVideoWorkflow",
    "SemiAutoWorkflow",
    "WorkflowState",
    "WorkflowConfig",
    "WorkflowMode",
    "VideoQuality",
    "create_full_auto_workflow",
    "create_semi_auto_workflow"
]
