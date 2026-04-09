"""
AI Agent模块 - 基于LangGraph的ReAct工具调用模式
全自动生成视频：对话 -> 理解需求 -> 调用工具链 -> 输出视频
"""
import json
import uuid
from typing import Dict, Any, List, Annotated, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import tools_condition

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

import sys
sys.path.insert(0, str(Path(__file__).parent))

from skills import (
    TextGenerationSkill, SelectRandomImageSkill,
    SpeechSynthesisSkill, VideoGenerationSkill,
    QualityEvaluationSkill
)
from ai_agent import VideoGenerationConfig
from config import API_CONFIG


@dataclass
class AgentState:
    """Agent状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    config: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    skill_results: Dict[str, Any] = field(default_factory=dict)


def create_video_generation_tools():
    """创建视频生成相关的LangChain工具"""
    
    @tool("generate_script", description="根据主题生成英文演讲稿。输入: topic(演讲主题), length(字数，默认300), difficulty(难度: elementary/middle_school/high_school/college_cet/english_major/native)")
    def generate_script(topic: str, length: int = 300, difficulty: str = "college_cet") -> str:
        """生成演讲稿"""
        skill = TextGenerationSkill()
        import asyncio
        result = asyncio.run(skill.execute({}, topic=topic, length=length, difficulty=difficulty))
        if result.success:
            return json.dumps({"success": True, "script": result.output.get("text", ""), "word_count": result.output.get("word_count", 0)})
        return json.dumps({"success": False, "error": result.error})
    
    @tool("select_anchor_image", description="选择主播形象图片。输入: gender(male/female), age(child/teen/young_adult/middle_aged/senior)")
    def select_anchor_image(gender: str = "female", age: str = "young_adult") -> str:
        """选择主播图片"""
        skill = SelectRandomImageSkill()
        import asyncio
        result = asyncio.run(skill.execute({}, gender=gender, age=age, style="formal"))
        if result.success:
            return json.dumps({"success": True, "image_path": result.output.get("image_path", "")})
        return json.dumps({"success": False, "error": result.error})
    
    @tool("synthesize_audio", description="将演讲稿转换为语音。输入: text(演讲稿文本), method(piper/xtts/minimax等TTS方法)")
    def synthesize_audio(text: str, method: str = "piper", reference_audio: str = None) -> str:
        """语音合成"""
        skill = SpeechSynthesisSkill()
        import asyncio
        params = {"text": text, "method": method}
        if reference_audio:
            params["reference_audio"] = reference_audio
        result = asyncio.run(skill.execute({}, **params))
        if result.success:
            return json.dumps({"success": True, "audio_path": result.output.get("audio_path", ""), "duration": result.output.get("duration", 0)})
        return json.dumps({"success": False, "error": result.error})
    
    @tool("generate_talking_video", description="根据音频和图片生成说话人视频。输入: audio_path(音频文件), image_path(图片文件), method(wav2lip/sadtalker)")
    def generate_talking_video(audio_path: str, image_path: str, method: str = "sadtalker") -> str:
        """生成说话人视频"""
        skill = VideoGenerationSkill()
        import asyncio
        result = asyncio.run(skill.execute({}, audio_path=audio_path, image_path=image_path, method=method))
        if result.success:
            return json.dumps({"success": True, "video_path": result.output.get("video_path", "")})
        return json.dumps({"success": False, "error": result.error})
    
    @tool("evaluate_video_quality", description="评估生成视频的质量。输入: video_path(视频文件路径)")
    def evaluate_video_quality(video_path: str) -> str:
        """质量评估"""
        skill = QualityEvaluationSkill()
        import asyncio
        result = asyncio.run(skill.execute({}, video_path=video_path))
        if result.success:
            return json.dumps({"success": True, "quality_score": result.output.get("quality_score", 0)})
        return json.dumps({"success": False, "error": result.error})
    
    @tool("confirm_complete", description="确认任务完成，向用户展示最终结果")
    def confirm_complete(video_path: str = None) -> str:
        """确认完成"""
        return json.dumps({"success": True, "message": "视频生成完成", "video_path": video_path or ""})
    
    return [
        generate_script,
        select_anchor_image,
        synthesize_audio,
        generate_talking_video,
        evaluate_video_quality,
        confirm_complete
    ]


def build_video_agent_graph():
    """构建视频生成Agent图"""
    tools = create_video_generation_tools()
    
    # MiniMax M2.7 使用 Anthropic API 兼容
    from langchain_anthropic import ChatAnthropic
    
    text_api = API_CONFIG.get("text_api", {})
    api_key = text_api.get("api_key", "")
    
    llm = ChatAnthropic(
        model="MiniMax-M2.7",
        anthropic_api_key=api_key,
        base_url="https://api.minimaxi.com/anthropic"
    )
    
    # 绑定工具
    llm_with_tools = llm.bind_tools(tools)
    
    # 构建图
    workflow = StateGraph(AgentState)
    
    # 入口节点：LLM决策
    def llm_node(state: AgentState) -> dict:
        new_messages = state.messages + [llm_with_tools.invoke(state.messages)]
        return {"messages": new_messages}
    
    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("llm")
    workflow.add_conditional_edges(
        "llm",
        tools_condition,
        {"tools": "tools", "__end__": END}
    )
    workflow.add_edge("tools", "llm")
    
    return workflow.compile(checkpointer=MemorySaver())


class VideoAgent:
    """视频生成Agent - 配置确认模式"""
    
    SYSTEM_PROMPT = """你是一个专业的AI英语演讲视频生成助手。

【核心原则：用户确认后通过点击按钮开始生成】
你的主要任务是理解用户需求并生成配置选项。**不要在对话中调用任何工具**，而是引导用户通过界面上的"确认并生成"按钮开始视频生成。

【工作流程】
1. 当用户提出生成视频的需求时：
   - 理解用户需求（主题、风格、难度等）
   - 用中文向用户展示配置选项
   - 告知用户可以修改配置或点击"确认并生成"按钮开始生成

2. 当用户说"确认开始生成"、"开始生成"或类似确认语时：
   - 不要调用工具！
   - 告诉用户：请点击界面上的"确认并生成"按钮开始生成
   - 或者用户可以直接点击按钮，无需再次确认

【配置选项】
- 主题(topic): 用户想要的演讲主题
- 难度(difficulty): elementary/middle_school/high_school/college_cet/english_major/native
- 风格(style): informative/motivational/persuasive/entertaining等
- 长度(length): 目标字数，默认300词

【重要原则】
- 永远不要在对话中调用工具！
- 每次回复后，告诉用户下一步操作
- 如果用户询问工具或生成流程，解释但不调用

请用中文回复用户。"""
    
    def __init__(self):
        self.graph = build_video_agent_graph()
        self.config = VideoGenerationConfig()
    
    def chat(self, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """处理用户消息"""
        messages = [SystemMessage(content=self.SYSTEM_PROMPT)]
        
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
        
        messages.append(HumanMessage(content=user_message))
        
        state = AgentState(
            messages=messages,
            config=self.config.to_dict(),
            is_complete=False,
            skill_results={}
        )
        
        thread_id = str(uuid.uuid4())
        
        # 运行图
        final_state = None
        for state_chunk in self.graph.stream(
            state,
            config={"configurable": {"thread_id": thread_id}}
        ):
            final_state = state_chunk
        
        if final_state:
            last_state = list(final_state.values())[-1]
            result_messages = last_state.get("messages", [])
            
            # 收集对话历史
            conversation = []
            for msg in result_messages:
                if isinstance(msg, HumanMessage):
                    content = msg.content
                    # 确保content是字符串
                    if not isinstance(content, str):
                        content = str(content) if content else ""
                    conversation.append({"role": "user", "content": content})
                elif isinstance(msg, AIMessage):
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content
                        # 确保content是字符串（有些LLM返回的是对象/数组）
                        if not isinstance(content, str):
                            if isinstance(content, list):
                                # 尝试提取文本内容
                                text_parts = []
                                for part in content:
                                    if isinstance(part, dict) and part.get('text'):
                                        text_parts.append(part['text'])
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                content = '\n'.join(text_parts)
                            elif isinstance(content, dict):
                                content = content.get('text', JSON.dumps(content))
                            else:
                                content = str(content)
                        conversation.append({"role": "assistant", "content": content})
            
            # 从对话中提取配置信息
            config = self._extract_config_from_conversation(conversation)
            
            # 确保response是字符串
            response_text = ""
            if conversation:
                last_content = conversation[-1].get("content", "")
                response_text = last_content if isinstance(last_content, str) else str(last_content)
            
            return {
                "success": True,
                "messages": conversation,
                "response": response_text,
                "config": config,
                "skill_results": last_state.get("skill_results", {}),
                "is_complete": last_state.get("is_complete", False)
            }
    
    def _extract_config_from_conversation(self, conversation: List[Dict]) -> Dict[str, Any]:
        """从对话历史中提取配置信息"""
        import re
        
        # 合并所有对话内容
        full_text = ""
        for msg in conversation:
            content = msg.get("content", "")
            if isinstance(content, str):
                full_text += content + "\n"
        
        config = {}
        
        # 提取主题 - 多种模式
        topic_patterns = [
            r'主题[：:]\s*([^\n|，|。]+)',
            r'topic[：:]\s*([^\n|，|。]+)',
            r'\*\*主题 \(Topic\)\*\*[^\n]*\|\s*([^\n|，|。]+)',
            r'关于\s*([^\n|，|。]+?)\s*的\s*英语\s*演讲',
        ]
        for pattern in topic_patterns:
            match = re.search(pattern, full_text)
            if match:
                config["topic"] = match.group(1).strip()
                break
        
        # 如果没找到，尝试从用户消息中提取
        if "topic" not in config:
            for msg in conversation:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    # 匹配"介绍XXX"或"关于XXX"或"XXX的英语演讲"
                    match = re.search(r'[介绍关于]([^\n|，|。]+)', content)
                    if match:
                        config["topic"] = match.group(1).strip()
                    else:
                        # 直接把用户消息作为主题
                        match = re.search(r'([^\n|，|。]+)', content)
                        if match:
                            config["topic"] = match.group(1).strip()[:50]  # 限制长度
                    break
        
        # 提取难度
        difficulty_map = {
            "小学": "elementary",
            "初中": "middle_school", 
            "高中": "high_school",
            "四六级": "college_cet",
            "大学": "college_cet",
            "专业": "english_major",
            "母语": "native",
            "elementary": "elementary",
            "middle_school": "middle_school",
            "high_school": "high_school",
            "college_cet": "college_cet",
            "english_major": "english_major",
            "native": "native"
        }
        for chinese, eng in difficulty_map.items():
            if chinese.lower() in full_text.lower():
                config["difficulty"] = eng
                break
        
        # 提取风格
        style_map = {
            "信息": "informative",
            "激励": "motivational",
            "说服": "persuasive",
            "娱乐": "entertaining"
        }
        for chinese, eng in style_map.items():
            if chinese in full_text:
                config["style"] = eng
                break
        
        # 提取长度
        length_match = re.search(r'(\d+)\s*词', full_text)
        if length_match:
            config["length"] = int(length_match.group(1))
        else:
            config["length"] = 300  # 默认300词
        
        # 如果没有找到主题，尝试从用户消息中提取
        if "topic" not in config:
            for msg in conversation:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    # 匹配"关于XXX"或"介绍XXX"
                    match = re.search(r'[关于介绍]([^\n，。]+)', content)
                    if match:
                        config["topic"] = match.group(1).strip()
                        break
        
        # 设置默认值
        if "difficulty" not in config:
            config["difficulty"] = "college_cet"
        if "style" not in config:
            config["style"] = "informative"
            
        return config
        
        return {"success": False, "error": "处理失败"}


def create_agent() -> VideoAgent:
    """创建Agent实例"""
    return VideoAgent()
