"""
AI Agent Skills 模块
定义Agent可调用的各种技能
"""
import json
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib


class SkillCategory(Enum):
    """技能分类"""
    TEXT = "text"           # 文本生成
    IMAGE = "image"         # 图像处理
    AUDIO = "audio"         # 语音合成
    VIDEO = "video"         # 视频生成
    EVAL = "evaluation"     # 质量评估
    UTILITY = "utility"     # 工具类


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    output: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class Skill(ABC):
    """技能基类"""
    
    def __init__(self, name: str, description: str, category: SkillCategory, 
                 input_schema: Dict[str, Any], output_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.category = category
        self.input_schema = input_schema  # 输入参数定义
        self.output_schema = output_schema  # 输出结果定义
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        """执行技能"""
        pass
    
    def validate_input(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """验证输入参数"""
        required = self.input_schema.get("required", [])
        for key in required:
            if key not in params:
                return False, f"缺少必需参数: {key}"
        return True, ""
    
    def get_schema(self) -> Dict[str, Any]:
        """获取技能定义（供Agent查看）"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }


@dataclass
class StudentProfile:
    """学生档案"""
    id: str
    name: str = ""
    topic: str = ""  # 演讲主题
    script: str = ""  # 生成的脚本
    audio_path: str = ""  # 音频路径
    image_path: str = ""  # 头像路径
    video_path: str = ""  # 最终视频路径
    quality_score: float = 0.0  # 质量评分
    feedback: str = ""  # 反馈修正


class ImageLibrary:
    """本地图片库管理"""
    
    def __init__(self, library_path: str = None):
        if library_path is None:
            library_path = Path(__file__).parent / "image_library"
        self.library_path = Path(library_path)
        self._images: List[Path] = []
        self._load_images()
    
    def _load_images(self):
        """加载图片库"""
        if not self.library_path.exists():
            self.library_path.mkdir(parents=True, exist_ok=True)
            return
        
        extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        seen = set()  # 用于去重
        for ext in extensions:
            for img in self.library_path.glob(f"*{ext}"):
                if img not in seen:
                    seen.add(img)
                    self._images.append(img)
    
    def get_random_image(self) -> Optional[str]:
        """随机获取一张图片"""
        if not self._images:
            return None
        return str(random.choice(self._images))
    
    def get_image_count(self) -> int:
        """获取图片库中图片数量"""
        return len(self._images)
    
    def refresh(self):
        """刷新图片库"""
        self._images.clear()
        self._load_images()


class SkillsRegistry:
    """技能注册中心"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, Skill] = {}
            cls._instance._student_profiles: List[StudentProfile] = []
            cls._instance._image_library = ImageLibrary()
        return cls._instance
    
    def register(self, skill: Skill):
        """注册技能"""
        self._skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self._skills.get(name)
    
    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """按分类获取技能"""
        return [s for s in self._skills.values() if s.category == category]
    
    def get_all_skills(self) -> List[Skill]:
        """获取所有技能"""
        return list(self._skills.values())
    
    def get_skill_schemas(self) -> List[Dict[str, Any]]:
        """获取所有技能的schema定义"""
        return [skill.get_schema() for skill in self._skills.values()]
    
    def get_image_library(self) -> ImageLibrary:
        """获取图片库"""
        return self._image_library
    
    def add_student(self, student: StudentProfile):
        """添加学生档案"""
        self._student_profiles.append(student)
    
    def get_students(self) -> List[StudentProfile]:
        """获取所有学生档案"""
        return self._student_profiles
    
    def get_student(self, student_id: str) -> Optional[StudentProfile]:
        """根据ID获取学生档案"""
        for student in self._student_profiles:
            if student.id == student_id:
                return student
        return None
    
    def update_student(self, student_id: str, **kwargs):
        """更新学生档案"""
        student = self.get_student(student_id)
        if student:
            for key, value in kwargs.items():
                if hasattr(student, key):
                    setattr(student, key, value)


# ============= 具体技能实现 =============

class TextGenerationSkill(Skill):
    """文本生成技能"""
    
    def __init__(self):
        super().__init__(
            name="generate_text",
            description="根据主题生成英文演讲稿。输入演讲主题、目标字数、难度级别，输出英文演讲文本。",
            category=SkillCategory.TEXT,
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "演讲主题"},
                    "length": {"type": "integer", "description": "目标字数", "default": 300},
                    "difficulty": {"type": "string", "enum": ["easy", "intermediate", "advanced"], "default": "intermediate"},
                    "style": {"type": "string", "enum": ["general", "business", "academic", "casual"], "default": "general"}
                },
                "required": ["topic"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "生成的演讲稿"},
                    "word_count": {"type": "integer", "description": "实际字数"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            # 验证输入
            valid, msg = self.validate_input(kwargs)
            if not valid:
                return SkillResult(success=False, error=msg)
            
            topic = kwargs.get("topic")
            length = kwargs.get("length", 300)
            difficulty = kwargs.get("difficulty", "intermediate")
            style = kwargs.get("style", "general")
            
            # 调用文本管理器生成
            from models.text import TextManager, SpeechRequest
            from config import API_CONFIG
            
            text_api_config = API_CONFIG.get("text_api", {})
            text_manager = TextManager(text_api_config)
            
            # 优先使用 AI 生成，失败时使用随机生成
            text = None
            error_msg = None
            for mode in ["ai_generate", "random"]:
                try:
                    request = SpeechRequest(
                        mode=mode,
                        topic=topic,
                        length=length,
                        difficulty=difficulty,
                        style=style
                    )
                    text = text_manager.get_text(request)
                    break
                except Exception as e:
                    error_msg = str(e)
                    continue
            
            if text is None:
                return SkillResult(success=False, error=f"文本生成失败: {error_msg}")
            
            word_count = len(text.split())
            
            return SkillResult(
                success=True,
                output={
                    "text": text,
                    "word_count": word_count
                },
                metadata={"topic": topic, "difficulty": difficulty}
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))


class TextFromFileSkill(Skill):
    """从文件读取文本技能"""
    
    def __init__(self):
        super().__init__(
            name="read_text_file",
            description="从本地文件读取文本内容。支持.txt, .docx, .pdf格式。",
            category=SkillCategory.TEXT,
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"}
                },
                "required": ["file_path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "文件文本内容"},
                    "char_count": {"type": "integer", "description": "字符数"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            file_path = kwargs.get("file_path")
            if not file_path:
                return SkillResult(success=False, error="缺少文件路径")
            
            path = Path(file_path)
            if not path.exists():
                return SkillResult(success=False, error=f"文件不存在: {file_path}")
            
            ext = path.suffix.lower()
            text = ""
            
            if ext == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif ext == '.docx':
                # 使用python-docx读取
                try:
                    from docx import Document
                    doc = Document(path)
                    text = '\n'.join([p.text for p in doc.paragraphs])
                except ImportError:
                    return SkillResult(success=False, error="python-docx库未安装")
            elif ext == '.pdf':
                # 使用PyPDF2读取
                try:
                    import PyPDF2
                    with open(path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ''
                        for page in reader.pages:
                            text += page.extract_text() + '\n'
                except ImportError:
                    return SkillResult(success=False, error="PyPDF2库未安装")
            else:
                return SkillResult(success=False, error=f"不支持的文件格式: {ext}")
            
            return SkillResult(
                success=True,
                output={
                    "text": text,
                    "char_count": len(text)
                }
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))


class SelectRandomImageSkill(Skill):
    """随机选择头像技能"""
    
    def __init__(self):
        super().__init__(
            name="select_random_image",
            description="从本地图片库随机选择一张图片作为人物头像。",
            category=SkillCategory.IMAGE,
            input_schema={
                "type": "object",
                "properties": {
                    "prefer_new": {"type": "boolean", "description": "是否优先选择未使用的图片", "default": True}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "选中的图片路径"},
                    "library_count": {"type": "integer", "description": "图片库总数"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            registry = SkillsRegistry()
            image_lib = registry.get_image_library()
            
            prefer_new = kwargs.get("prefer_new", True)
            selected = None
            
            if prefer_new:
                # 优先选择未使用的图片
                used_images = set()
                for student in registry.get_students():
                    if student.image_path:
                        used_images.add(student.image_path)
                
                available = [img for img in image_lib._images if str(img) not in used_images]
                if available:
                    selected = random.choice(available)
            
            if selected is None:
                selected = image_lib.get_random_image()
            
            if selected is None:
                return SkillResult(success=False, error="图片库为空")
            
            return SkillResult(
                success=True,
                output={
                    "image_path": str(selected),
                    "library_count": image_lib.get_image_count()
                }
            )
        except Exception as e:
            return SkillResult(success=False, error=str(e))


class SpeechSynthesisSkill(Skill):
    """语音合成技能"""

    def __init__(self):
        super().__init__(
            name="synthesize_speech",
            description="将文本转换为语音。输入文本和TTS方法，输出音频文件路径。",
            category=SkillCategory.AUDIO,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要转换的文本"},
                    "method": {"type": "string", "enum": ["piper", "xtts", "online", "minimax", "kokoro"], "default": "piper"},
                    "reference_audio": {"type": "string", "description": "参考音频（用于XTTS音色克隆）"},
                    "minimax_voice_id": {"type": "string", "description": "MiniMax音色ID"},
                    "wer_threshold": {"type": "integer", "description": "WER阈值", "default": 15}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string", "description": "生成的音频文件路径"},
                    "duration": {"type": "number", "description": "音频时长（秒）"}
                }
            }
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            valid, msg = self.validate_input(kwargs)
            if not valid:
                return SkillResult(success=False, error=msg)

            text = kwargs.get("text")
            method = kwargs.get("method", "piper")
            reference_audio = kwargs.get("reference_audio")
            minimax_voice_id = kwargs.get("minimax_voice_id", "English_Graceful_Lady")
            wer_threshold = kwargs.get("wer_threshold", 15)

            # 创建输出目录
            from config import PROJECT_ROOT
            import uuid
            timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
            output_dir = PROJECT_ROOT / "output" / "agent" / timestamp / "audio"
            output_dir.mkdir(parents=True, exist_ok=True)

            audio_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
            output_path = str(output_dir / audio_filename)

            # 调用TTS管理器
            from models.tts import TTSManager
            from config import API_CONFIG
            tts_manager = TTSManager(API_CONFIG)

            # 如果使用MiniMax TTS，设置音色ID
            if method == "minimax":
                tts_manager.api_config["voice_id"] = minimax_voice_id

            result = tts_manager.synthesize(
                text=text,
                method=method,
                output_filename=output_path,
                reference_wav=reference_audio,
                wer_threshold=wer_threshold
            )

            if result.success:
                return SkillResult(
                    success=True,
                    output={
                        "audio_path": result.audio_path,
                        "duration": result.duration
                    }
                )
            else:
                return SkillResult(success=False, error=result.error_msg)

        except Exception as e:
            return SkillResult(success=False, error=str(e))


class VideoGenerationSkill(Skill):
    """视频生成技能"""
    
    def __init__(self):
        super().__init__(
            name="generate_video",
            description="根据音频和图像生成说话视频。使用Wav2Lip或SadTalker。",
            category=SkillCategory.VIDEO,
            input_schema={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "人物头像路径"},
                    "audio_path": {"type": "string", "description": "语音音频路径"},
                    "method": {"type": "string", "enum": ["wav2lip", "sadtalker"], "default": "wav2lip"},
                    "fp16": {"type": "boolean", "description": "是否启用FP16加速（SadTalker加速1.5-1.8倍）", "default": True}
                },
                "required": ["image_path", "audio_path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "生成的视频路径"},
                    "duration": {"type": "number", "description": "视频时长（秒）"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            valid, msg = self.validate_input(kwargs)
            if not valid:
                return SkillResult(success=False, error=msg)
            
            image_path = kwargs.get("image_path")
            audio_path = kwargs.get("audio_path")
            method = kwargs.get("method", "wav2lip")
            fp16 = kwargs.get("fp16", True)  # 默认启用FP16加速
            
            # 创建输出目录
            from config import PROJECT_ROOT
            import uuid
            timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
            output_dir = PROJECT_ROOT / "output" / "agent" / timestamp / "video"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            video_filename = f"{method}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = str(output_dir / video_filename)
            
            # 调用视频管理器
            from models.video import VideoManager
            video_manager = VideoManager()
            
            # 只有SadTalker支持fp16参数，Wav2Lip不支持
            video_kwargs = {
                "image_path": image_path,
                "audio_path": audio_path,
                "method": method,
                "output_path": output_path
            }
            if method == "sadtalker":
                video_kwargs["fp16"] = fp16
            
            result = video_manager.generate_video(**video_kwargs)
            
            if result.success:
                return SkillResult(
                    success=True,
                    output={
                        "video_path": result.video_path,
                        "duration": result.duration
                    },
                    metadata={"method": method, "resolution": f"{result.width}x{result.height}"}
                )
            else:
                return SkillResult(success=False, error=result.error)
                
        except Exception as e:
            return SkillResult(success=False, error=str(e))


class QualityEvaluationSkill(Skill):
    """质量评估技能"""
    
    def __init__(self):
        super().__init__(
            name="evaluate_quality",
            description="评估生成的视频质量，包括音频质量、唇形同步质量等。",
            category=SkillCategory.EVAL,
            input_schema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "视频路径"},
                    "audio_path": {"type": "string", "description": "音频路径（用于对比）"}
                },
                "required": ["video_path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "quality_score": {"type": "number", "description": "质量评分 0-100"},
                    "issues": {"type": "array", "description": "发现的问题列表"},
                    "suggestions": {"type": "array", "description": "改进建议"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            video_path = kwargs.get("video_path")
            if not video_path:
                return SkillResult(success=False, error="缺少视频路径")
            
            path = Path(video_path)
            if not path.exists():
                return SkillResult(success=False, error=f"视频文件不存在: {video_path}")
            
            # 简单的质量评估（基于文件大小、分辨率等）
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            duration = frame_count / fps if fps > 0 else 0
            file_size_mb = path.stat().st_size / (1024 * 1024)
            
            # 基础评分
            quality_score = 70.0
            issues = []
            suggestions = []
            
            # 检查分辨率
            if width < 512 or height < 512:
                quality_score -= 10
                issues.append("分辨率过低")
                suggestions.append("建议使用更高分辨率的源图")
            
            # 检查帧率
            if fps < 24:
                quality_score -= 5
                issues.append("帧率偏低")
                suggestions.append("建议使用24fps以上")
            
            # 检查视频时长
            if duration < 10:
                quality_score -= 5
                issues.append("视频时长过短")
            
            # 检查文件大小
            if file_size_mb < 0.5:
                quality_score -= 5
                issues.append("视频文件偏小，可能压缩过度")
            
            quality_score = max(0, min(100, quality_score))
            
            return SkillResult(
                success=True,
                output={
                    "quality_score": quality_score,
                    "issues": issues,
                    "suggestions": suggestions,
                    "details": {
                        "resolution": f"{width}x{height}",
                        "fps": fps,
                        "duration": duration,
                        "file_size_mb": round(file_size_mb, 2)
                    }
                }
            )
                
        except Exception as e:
            return SkillResult(success=False, error=str(e))


class FeedbackRefinementSkill(Skill):
    """反馈修正技能"""
    
    def __init__(self):
        super().__init__(
            name="refine_with_feedback",
            description="根据质量评估反馈，对视频进行修正或生成改进建议。",
            category=SkillCategory.UTILITY,
            input_schema={
                "type": "object",
                "properties": {
                    "original_text": {"type": "string", "description": "原始文本"},
                    "quality_result": {"type": "object", "description": "质量评估结果"},
                    "refine_type": {"type": "string", "enum": ["script", "video"], "default": "video"}
                },
                "required": ["original_text", "quality_result"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "refined_text": {"type": "string", "description": "修正后的文本（如适用）"},
                    "suggestions": {"type": "array", "description": "改进建议"}
                }
            }
        )
    
    async def execute(self, context: Dict[str, Any], **kwargs) -> SkillResult:
        try:
            original_text = kwargs.get("original_text")
            quality_result = kwargs.get("quality_result", {})
            refine_type = kwargs.get("refine_type", "video")
            
            suggestions = quality_result.get("suggestions", [])
            issues = quality_result.get("issues", [])
            
            if not suggestions and not issues:
                return SkillResult(
                    success=True,
                    output={
                        "refined_text": original_text,
                        "suggestions": ["质量良好，无需修正"]
                    }
                )
            
            # 根据问题类型生成建议
            refined_suggestions = []
            
            for issue in issues:
                if "分辨率" in issue:
                    refined_suggestions.append("建议使用更高分辨率的头像图片（至少512x512）")
                elif "帧率" in issue:
                    refined_suggestions.append("视频帧率偏低，可尝试调整Wav2Lip参数")
                elif "时长" in issue:
                    refined_suggestions.append("演讲时长偏短，建议增加内容或调整语速")
            
            # 如果问题严重且是视频问题，建议重试
            quality_score = quality_result.get("quality_score", 100)
            if quality_score < 60 and refine_type == "video":
                refined_suggestions.append("视频质量较低，建议更换头像图片或重新生成")
            
            return SkillResult(
                success=True,
                output={
                    "refined_text": original_text,  # 目前文本不做修改
                    "suggestions": refined_suggestions,
                    "needs_regeneration": quality_score < 60
                }
            )
                
        except Exception as e:
            return SkillResult(success=False, error=str(e))


def register_all_skills():
    """注册所有技能到注册中心"""
    registry = SkillsRegistry()
    
    # 注册技能
    skills = [
        TextGenerationSkill(),
        TextFromFileSkill(),
        SelectRandomImageSkill(),
        SpeechSynthesisSkill(),
        VideoGenerationSkill(),
        QualityEvaluationSkill(),
        FeedbackRefinementSkill(),
    ]
    
    for skill in skills:
        registry.register(skill)
    
    return registry


# 方便导入的技能实例
def get_skills_registry() -> SkillsRegistry:
    return SkillsRegistry()


from datetime import datetime
