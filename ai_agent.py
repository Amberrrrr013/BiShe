"""
全自动AI Agent模块
基于LangGraph的ReAct模式，实现与用户对话后自动生成视频
"""
import asyncio
import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal, Annotated, Sequence
from pathlib import Path
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).parent))

from skills import (
    SkillsRegistry, SkillResult, StudentProfile,
    register_all_skills, get_skills_registry,
    TextGenerationSkill, TextFromFileSkill, SelectRandomImageSkill,
    SpeechSynthesisSkill, VideoGenerationSkill,
    QualityEvaluationSkill, FeedbackRefinementSkill
)
from config import API_CONFIG


class AgentState(dict):
    """Agent状态类"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    extracted_config: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    current_skill_result: Any = None
    conversation_turns: int = 0
    skill_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    pending_modification: Optional[str] = None  # 当前待确认的修改项
    modification_confirmed: bool = False       # 修改是否已确认


class VideoGenerationConfig:
    """视频生成配置类"""
    def __init__(self):
        self.topic: Optional[str] = None
        self.length: int = 300
        self.difficulty: str = "college_cet"
        self.style: str = "informative"
        self.image_gender: str = "female"
        self.image_age: str = "young_adult"
        self.image_expression: str = "happy"
        self.image_background: str = "office"
        self.tts_method: str = "piper"
        self.video_method: str = "sadtalker"
        self.reference_audio: Optional[str] = None
        self.image_path: Optional[str] = None
        self.model: str = "glm"
        self.wer_threshold: int = 15
        self.add_subtitles: bool = True
        self.student_count: int = 1
        self.source_file: Optional[str] = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "length": self.length,
            "difficulty": self.difficulty,
            "style": self.style,
            "image_gender": self.image_gender,
            "image_age": self.image_age,
            "image_expression": self.image_expression,
            "image_background": self.image_background,
            "tts_method": self.tts_method,
            "video_method": self.video_method,
            "reference_audio": self.reference_audio,
            "image_path": self.image_path,
            "model": self.model,
            "wer_threshold": self.wer_threshold,
            "add_subtitles": self.add_subtitles,
            "student_count": self.student_count,
            "source_file": self.source_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoGenerationConfig":
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


@tool
def extract_requirements(user_message: str) -> str:
    """
    从用户消息中提取视频生成需求参数。
    当用户提供演讲主题、风格偏好、或其他视频生成相关需求时使用此工具。
    
    返回JSON格式的配置参数，包括：
    - topic: 演讲主题
    - length: 目标字数
    - difficulty: 英语难度
    - style: 演讲风格
    - image_gender: 主播性别偏好
    - tts_method: 语音合成方法
    - video_method: 视频生成方法
    """
    return "配置参数已提取"


@tool
def generate_english_speech(topic: str, length: int = 300, difficulty: str = "college_cet", 
                           style: str = "informative", model: str = "glm") -> str:
    """
    生成英文演讲稿。
    
    参数:
    - topic: 演讲主题
    - length: 目标字数（默认300）
    - difficulty: 英语难度 (elementary/middle_school/high_school/college_cet/english_major/native)
    - style: 演讲风格 (informative/motivational/persuasive/entertaining/ceremonial/keynote/demonstration/tributary/controversial/storytelling)
    - model: 使用的AI模型 (glm/minimax)
    
    返回生成的英文演讲稿
    """
    registry = get_skills_registry()
    skill = registry.get_skill("generate_text")
    
    if not skill:
        return "错误: 文本生成技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(
        context={},
        topic=topic,
        length=length,
        difficulty=difficulty,
        style=style
    ))
    loop.close()
    
    if result.success:
        return result.output.get("text", "")
    else:
        return f"错误: {result.error}"


@tool
def select_character_image(prefer_new: bool = True) -> str:
    """
    从本地图片库随机选择一张人物头像图片。
    
    参数:
    - prefer_new: 是否优先选择未使用过的图片（默认True）
    
    返回选中的图片路径
    """
    registry = get_skills_registry()
    skill = registry.get_skill("select_random_image")
    
    if not skill:
        return "错误: 图片选择技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(context={}, prefer_new=prefer_new))
    loop.close()
    
    if result.success:
        return result.output.get("image_path", "")
    else:
        return f"错误: {result.error}"


@tool
def synthesize_speech(text: str, method: str = "piper", 
                      reference_audio: Optional[str] = None,
                      minimax_voice_id: str = "English_Graceful_Lady",
                      kokoro_voice: str = "af_heart") -> str:
    """
    将英文文本转换为语音。
    
    参数:
    - text: 要转换的英文文本
    - method: 语音合成方法 (piper/xtts/online/minimax/kokoro)
    - reference_audio: XTTS参考音频路径（用于音色克隆）
    - minimax_voice_id: MiniMax音色ID
    - kokoro_voice: Kokoro音色名称
    
    返回生成的音频文件路径
    """
    registry = get_skills_registry()
    skill = registry.get_skill("synthesize_speech")
    
    if not skill:
        return "错误: 语音合成技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(
        context={},
        text=text,
        method=method,
        reference_audio=reference_audio,
        minimax_voice_id=minimax_voice_id
    ))
    loop.close()
    
    if result.success:
        return result.output.get("audio_path", "")
    else:
        return f"错误: {result.error}"


@tool
def generate_talking_video(image_path: str, audio_path: str, 
                          method: str = "sadtalker") -> str:
    """
    根据头像图片和语音生成说话视频。
    
    参数:
    - image_path: 人物头像图片路径
    - audio_path: 语音音频文件路径
    - method: 视频生成方法 (wav2lip/sadtalker)
    
    返回生成的视频文件路径
    """
    registry = get_skills_registry()
    skill = registry.get_skill("generate_video")
    
    if not skill:
        return "错误: 视频生成技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(
        context={},
        image_path=image_path,
        audio_path=audio_path,
        method=method
    ))
    loop.close()
    
    if result.success:
        return result.output.get("video_path", "")
    else:
        return f"错误: {result.error}"


@tool
def evaluate_video_quality(video_path: str, audio_path: Optional[str] = None) -> str:
    """
    评估生成的视频质量。
    
    参数:
    - video_path: 视频文件路径
    - audio_path: 音频文件路径（可选，用于对比）
    
    返回质量评估结果JSON字符串
    """
    registry = get_skills_registry()
    skill = registry.get_skill("evaluate_quality")
    
    if not skill:
        return "错误: 质量评估技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(
        context={},
        video_path=video_path,
        audio_path=audio_path
    ))
    loop.close()
    
    if result.success:
        return json.dumps(result.output, ensure_ascii=False)
    else:
        return f"错误: {result.error}"


@tool
def refine_based_on_feedback(original_text: str, quality_result: str) -> str:
    """
    根据质量评估反馈提供改进建议。
    
    参数:
    - original_text: 原始演讲文本
    - quality_result: 质量评估结果（JSON字符串）
    
    返回改进建议JSON字符串
    """
    registry = get_skills_registry()
    skill = registry.get_skill("refine_with_feedback")
    
    if not skill:
        return "错误: 反馈修正技能未找到"
    
    try:
        quality_dict = json.loads(quality_result)
    except:
        quality_dict = {"quality_score": 50, "issues": [], "suggestions": []}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(
        context={},
        original_text=original_text,
        quality_result=quality_dict
    ))
    loop.close()
    
    if result.success:
        return json.dumps(result.output, ensure_ascii=False)
    else:
        return f"错误: {result.error}"


@tool
def read_text_file(file_path: str) -> str:
    """
    从本地文件读取文本内容。
    
    参数:
    - file_path: 文件路径
    
    返回文件中的文本内容
    """
    registry = get_skills_registry()
    skill = registry.get_skill("read_text_file")
    
    if not skill:
        return "错误: 文件读取技能未找到"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(skill.execute(context={}, file_path=file_path))
    loop.close()
    
    if result.success:
        return result.output.get("text", "")
    else:
        return f"错误: {result.error}"


def get_all_tools() -> List:
    """获取所有可用工具"""
    return [
        extract_requirements,
        generate_english_speech,
        select_character_image,
        synthesize_speech,
        generate_talking_video,
        evaluate_video_quality,
        refine_based_on_feedback,
        read_text_file
    ]


def get_llm(model_name: str = "glm"):
    """获取LLM实例"""
    if model_name == "minimax":
        return ChatOpenAI(
            model="MiniMax-M2.5",
            api_key=API_CONFIG.get("text_api", {}).get("api_key"),
            base_url=API_CONFIG.get("text_api", {}).get("base_url")
        ).bind_tools(get_all_tools())
    else:
        return ChatOpenAI(
            model="glm-4-flash-250414",
            api_key=API_CONFIG.get("text_api", {}).get("api_key") or os.getenv("GLM_API_KEY", ""),
            base_url=API_CONFIG.get("text_api", {}).get("base_url", "https://open.bigmodel.cn/api/paas/v4")
        ).bind_tools(get_all_tools())


class FullAutoAgent:
    """全自动AI Agent - 仅对话提取配置，不执行工具"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.registry = register_all_skills()
        self.llm = get_llm(self.config.get("model", "glm"))
        self.checkpointer = MemorySaver()
        
        self.graph = self._build_graph()
        
        self.current_config = VideoGenerationConfig()
        self.execution_history: List[Dict[str, Any]] = []
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图 - 仅对话，不执行工具"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze", self._analyze_node)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _analyze_node(self, state: AgentState) -> AgentState:
        """分析节点 - LLM分析用户意图并决定下一步"""
        system_prompt = SystemMessage(content=self._build_system_prompt_with_config())
        
        messages = [system_prompt] + list(state.get("messages", []))
        
        response = self.llm.invoke(messages)
        
        state["messages"] = state.get("messages", []) + [response]
        state["conversation_turns"] = state.get("conversation_turns", 0) + 1
        
        # 从回复中提取配置
        if hasattr(response, 'content'):
            self._parse_config_from_result(response.content)
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """判断是否继续执行（基于LangGraph课程模式）"""
        messages = state.get("messages", [])
        if not messages:
            return "end"
        
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        return "end"
    
    def _execute_skill_node(self, state: AgentState) -> AgentState:
        """执行技能节点"""
        messages = state.get("messages", [])
        if not messages:
            return state
        
        last_message = messages[-1]
        if not hasattr(last_message, "tool_calls"):
            return state
        
        results = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            
            tool_result = self._execute_tool(tool_name, tool_args)
            results.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call.get("id", "")
            ))
            
    def _parse_config_from_result(self, content: str):
        """从结果中解析配置 - 优先JSON，失败时从文本提取主题"""
        if "{" in content and "}" in content:
            try:
                start_idx = content.rfind('{')
                end_idx = content.rfind('}') + 1
                if start_idx < end_idx:
                    json_str = content[start_idx:end_idx]
                    config_dict = json.loads(json_str)
                    for key, value in config_dict.items():
                        if hasattr(self.current_config, key):
                            setattr(self.current_config, key, value)
                    # JSON解析成功则返回
                    return
            except json.JSONDecodeError:
                pass
        
        # JSON解析失败时，从对话文本中提取主题
        # 匹配 "主题确定为XXX" 或 "主题已更新为XXX" 等模式
        topic_match = re.search(r'主题确定为(.+?)[。\s]', content)
        if topic_match:
            topic = topic_match.group(1).strip()
            if topic and len(topic) > 1:
                self.current_config.topic = topic
                return
        
        topic_match = re.search(r'主题已更新为(.+?)[。\s]', content)
        if topic_match:
            topic = topic_match.group(1).strip()
            if topic and len(topic) > 1:
                self.current_config.topic = topic
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个AI视频生成配置助手。

你的任务是从用户对话中提取配置，并严格按格式返回JSON。

【关键规则】
1. 每次回复末尾必须包含JSON块
2. JSON格式：{"topic": "主题", "is_ready": false, ...}
3. 没有JSON块你的回复无效！

【配置选项】
- topic: 演讲主题（从用户描述中提取）
- student_count: 数量（默认1）
- difficulty: 难度（elementary/middle_school/high_school/college_cet/english_major/native）
- style: 风格（informative/motivational/persuasive/entertaining/ceremonial/keynote/demonstration/tributary/controversial/storytelling）
- image_gender: 性别（female/male）
- image_age: 年龄（child/teen/young_adult/middle_aged/senior）
- image_expression: 表情（happy/sad/angry/passionate/calm/surprised）
- image_background: 背景（office/classroom/studio/outdoor/library/starry/beach/city/park/nature）

【回复格式示例】
用户：我想做一个关于AI的英语演讲
回复：好的，我来帮你制作AI英语演讲视频。
```json
{"topic": "AI", "student_count": 1, "difficulty": "college_cet", "style": "informative", "image_gender": "female", "image_age": "young_adult", "image_expression": "happy", "image_background": "office", "is_ready": false}
```"""

    def _build_system_prompt_with_config(self) -> str:
        """构建包含当前配置的系统提示词"""
        base_prompt = self._get_system_prompt()
        current = self.current_config
        config_info = f"""

## 当前配置状态（每次回复时请参考）
- topic: {current.topic or '未指定'}
- length: {current.length}
- difficulty: {current.difficulty}
- style: {current.style}
- image_gender: {current.image_gender}
- image_age: {current.image_age}
- image_expression: {current.image_expression}
- image_background: {current.image_background}
- student_count: {current.student_count}

当用户提到主播形象时（如"男性"、"小孩"、"青少年"等），记得更新对应配置。
"""
        return base_prompt + config_info

    def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """处理用户消息"""
        messages = []
        
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
        
        messages.append(HumanMessage(content=user_message))
        
        state = AgentState(
            messages=messages,
            extracted_config=self.current_config.to_dict(),
            is_complete=False,
            skill_execution_log=[]
        )
        
        thread_id = str(uuid.uuid4())
        
        final_state = None
        for state_chunk in self.graph.stream(
            state,
            config={"configurable": {"thread_id": thread_id}}
        ):
            final_state = state_chunk
        
        if final_state:
            last_state = list(final_state.values())[-1] if final_state else state
            messages = last_state.get("messages", [])
            
            # 从 AI 的最后一条回复中提取配置
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and hasattr(msg, 'content'):
                    self._parse_config_from_result(msg.content)
                    break
            
            # 也从用户消息中提取配置
            self._parse_config_from_result(user_message)
            
            return {
                "success": True,
                "messages": messages,
                "config": self.current_config.to_dict(),
                "execution_history": self.execution_history,
                "is_complete": last_state.get("is_complete", False)
            }
        
        return {"success": False, "error": "处理失败"}
    
    def chat_stream(self, user_message: str, conversation_history: Optional[List[Dict]] = None):
        """流式处理用户消息"""
        messages = []
        
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
        
        messages.append(HumanMessage(content=user_message))
        
        state = AgentState(
            messages=messages,
            extracted_config=self.current_config.to_dict(),
            is_complete=False,
            skill_execution_log=[]
        )
        
        thread_id = str(uuid.uuid4())
        
        for state_chunk in self.graph.stream(
            state,
            config={"configurable": {"thread_id": thread_id}}
        ):
            yield state_chunk


def create_agent(config: Optional[Dict[str, Any]] = None) -> FullAutoAgent:
    """创建Agent实例"""
    return FullAutoAgent(config)
