"""
AI Agent 工作流
基于LangGraph的智能体工作流，实现多模态内容生成
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from skills import (
    SkillsRegistry, SkillResult, StudentProfile,
    register_all_skills, get_skills_registry,
    TextGenerationSkill, SelectRandomImageSkill, 
    SpeechSynthesisSkill, VideoGenerationSkill,
    QualityEvaluationSkill, FeedbackRefinementSkill
)


class AgentState(TypedDict):
    """Agent状态"""
    # 任务配置
    topic: str  # 主题（可以为多个学生不同主题）
    topics_list: List[str]  # 多个主题（如果有）
    student_count: int  # 学生数量（视频数量）
    
    # 当前处理的学号
    current_student_index: int
    current_student_id: str
    
    # 流程控制
    current_phase: str  # text/image/audio/video/evaluation/refinement
    next_action: str  # 下一步动作
    loop_count: int  # 循环次数（防止无限循环）
    
    # 结果存储
    students: Dict[str, Dict]  # 所有学生结果
    current_result: Dict[str, Any]  # 当前学生结果
    
    # 消息/日志
    messages: List[str]
    errors: List[str]
    
    # 完成标志
    is_complete: bool
    is_error: bool


class AgentWorkflow:
    """AI Agent 工作流"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.registry = register_all_skills()
        
        # 初始化图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_text", self._generate_text_node)
        workflow.add_node("select_image", self._select_image_node)
        workflow.add_node("synthesize_audio", self._synthesize_audio_node)
        workflow.add_node("generate_video", self._generate_video_node)
        workflow.add_node("evaluate_quality", self._evaluate_quality_node)
        workflow.add_node("handle_feedback", self._handle_feedback_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # 设置边
        workflow.set_entry_point("initialize")
        
        # 条件边
        workflow.add_conditional_edges(
            "initialize",
            self._should_use_file,
            {
                "file": "generate_text",
                "topic": "generate_text"
            }
        )
        
        # 主循环：文本 -> 图片 -> 音频 -> 视频 -> 评估 -> (反馈) -> 下一学生或完成
        workflow.add_edge("generate_text", "select_image")
        workflow.add_edge("select_image", "synthesize_audio")
        workflow.add_edge("synthesize_audio", "generate_video")
        workflow.add_edge("generate_video", "evaluate_quality")
        
        workflow.add_conditional_edges(
            "evaluate_quality",
            self._check_quality,
            {
                "retry": "handle_feedback",
                "next_student": "finalize",
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "handle_feedback",
            self._should_regenerate,
            {
                "retry": "generate_video",
                "skip": "finalize"
            }
        )
        
        workflow.add_conditional_edges(
            "finalize",
            self._should_continue,
            {
                "next": "generate_text",
                "complete": END
            }
        )
        
        return workflow.compile(checkpointer=MemorySaver())
    
    def _should_use_file(self, state: AgentState) -> str:
        """判断是否使用文件输入"""
        if state.get("topics_list") and len(state["topics_list"]) > 0:
            return "topic"
        
        # 检查是否有文件路径在配置中
        if self.config.get("source_file"):
            return "file"
        return "topic"
    
    def _initialize_node(self, state: AgentState) -> AgentState:
        """初始化节点"""
        state["messages"].append("Agent工作流启动")
        
        # 确定学生数量和主题
        topics_list = state.get("topics_list", [])
        if topics_list:
            state["student_count"] = len(topics_list)
        else:
            topic = state.get("topic", "")
            # 尝试分析主题，如果包含"50个"等信息，生成多个主题
            if "50" in topic or "五十" in topic:
                state["student_count"] = 50
            elif "30" in topic or "三十" in topic:
                state["student_count"] = 30
            elif "20" in topic or "二十" in topic:
                state["student_count"] = 20
            elif "10" in topic or "十" in topic:
                state["student_count"] = 10
            else:
                state["student_count"] = 1
            
            # 生成多个主题变体
            base_topic = topic.strip()
            state["topics_list"] = [f"{base_topic} - #{i+1}" for i in range(state["student_count"])]
        
        state["current_student_index"] = 0
        state["current_phase"] = "initialize"
        state["loop_count"] = 0
        state["is_complete"] = False
        
        # 初始化学生数据
        state["students"] = {}
        
        return state
    
    def _generate_text_node(self, state: AgentState) -> AgentState:
        """生成文本"""
        idx = state["current_student_index"]
        topic = state["topics_list"][idx] if idx < len(state["topics_list"]) else state["topic"]
        
        state["messages"].append(f"[学生 {idx+1}/{state['student_count']}] 生成文本: {topic}")
        state["current_phase"] = "text"
        
        # 使用skill生成文本
        skill = self.registry.get_skill("generate_text")
        
        # 确定参数
        length = self.config.get("length", 300)
        difficulty = self.config.get("difficulty", "intermediate")
        
        # 异步执行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(
            topic=topic,
            length=length,
            difficulty=difficulty
        ))
        loop.close()
        
        if result.success:
            text = result.output["text"]
            student_id = f"student_{idx+1}_{uuid.uuid4().hex[:4]}"
            
            state["students"][student_id] = {
                "id": student_id,
                "index": idx,
                "topic": topic,
                "text": text,
                "word_count": result.output.get("word_count", len(text.split())),
                "status": "text_generated"
            }
            state["current_student_id"] = student_id
            state["messages"].append(f"文本生成成功: {len(text)} 字符")
        else:
            state["errors"].append(f"文本生成失败: {result.error}")
            state["is_error"] = True
        
        return state
    
    def _select_image_node(self, state: AgentState) -> AgentState:
        """选择图片"""
        state["current_phase"] = "image"
        student_id = state["current_student_id"]
        
        # 优先使用配置的固定图片，否则随机选择
        if self.config.get("image_path"):
            image_path = self.config["image_path"]
            library_count = 0
            state["messages"].append(f"使用指定图片: {image_path}")
        else:
            skill = self.registry.get_skill("select_random_image")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(skill.execute(prefer_new=True))
            loop.close()
            
            if result.success:
                image_path = result.output["image_path"]
                library_count = result.output.get("library_count", 0)
                state["messages"].append(f"随机选择图片: {image_path} (库中{library_count}张)")
            else:
                state["errors"].append(f"图片选择失败: {result.error}")
                state["is_error"] = True
                return state
        
        state["students"][student_id]["image_path"] = image_path
        state["students"][student_id]["status"] = "image_selected"
        
        return state
    
    def _synthesize_audio_node(self, state: AgentState) -> AgentState:
        """合成语音"""
        state["current_phase"] = "audio"
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        state["messages"].append(f"开始语音合成...")
        
        skill = self.registry.get_skill("synthesize_speech")
        
        method = self.config.get("tts_method", "piper")
        reference_audio = self.config.get("reference_audio")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(
            text=student["text"],
            method=method,
            reference_audio=reference_audio
        ))
        loop.close()
        
        if result.success:
            student["audio_path"] = result.output["audio_path"]
            student["audio_duration"] = result.output.get("duration", 0)
            student["status"] = "audio_synthesized"
            state["messages"].append(f"语音合成成功: {student['audio_duration']:.1f}秒")
        else:
            state["errors"].append(f"语音合成失败: {result.error}")
            state["is_error"] = True
        
        return state
    
    def _generate_video_node(self, state: AgentState) -> AgentState:
        """生成视频"""
        state["current_phase"] = "video"
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        state["messages"].append(f"开始视频生成...")
        
        skill = self.registry.get_skill("generate_video")
        
        # 优先使用wav2lip
        method = self.config.get("video_method", "wav2lip")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(
            image_path=student["image_path"],
            audio_path=student["audio_path"],
            method=method
        ))
        loop.close()
        
        if result.success:
            student["video_path"] = result.output["video_path"]
            student["video_duration"] = result.output.get("duration", 0)
            student["video_method"] = method
            student["status"] = "video_generated"
            state["messages"].append(f"视频生成成功: {method} {student['video_duration']:.1f}秒")
        else:
            state["errors"].append(f"视频生成失败: {result.error}")
            state["is_error"] = True
        
        return state
    
    def _evaluate_quality_node(self, state: AgentState) -> AgentState:
        """评估质量"""
        state["current_phase"] = "evaluation"
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        state["messages"].append(f"开始质量评估...")
        
        skill = self.registry.get_skill("evaluate_quality")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(
            video_path=student["video_path"],
            audio_path=student["audio_path"]
        ))
        loop.close()
        
        if result.success:
            quality = result.output
            student["quality_score"] = quality.get("quality_score", 0)
            student["quality_issues"] = quality.get("issues", [])
            student["quality_suggestions"] = quality.get("suggestions", [])
            student["status"] = "quality_evaluated"
            state["messages"].append(f"质量评分: {student['quality_score']:.1f}/100")
            
            if student["quality_issues"]:
                state["messages"].append(f"发现问题: {', '.join(student['quality_issues'])}")
        else:
            state["errors"].append(f"质量评估失败: {result.error}")
            student["quality_score"] = 50  # 默认分数
            student["quality_issues"] = ["评估失败"]
        
        return state
    
    def _check_quality(self, state: AgentState) -> str:
        """检查质量决定下一步"""
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        # 增加循环计数
        state["loop_count"] = state.get("loop_count", 0) + 1
        
        # 如果循环次数过多，直接跳过
        if state["loop_count"] > 50:
            state["messages"].append("达到最大循环次数，跳出")
            return "complete"
        
        quality_score = student.get("quality_score", 0)
        
        # 质量低于60且循环次数不超过3次，可以重试
        if quality_score < 60 and state["loop_count"] < 3:
            return "retry"
        
        # 质量OK或已达到重试上限，进入下一学生
        return "next_student"
    
    def _handle_feedback_node(self, state: AgentState) -> AgentState:
        """处理反馈"""
        state["current_phase"] = "feedback"
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        state["messages"].append(f"处理质量反馈...")
        
        skill = self.registry.get_skill("refine_with_feedback")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(skill.execute(
            original_text=student["text"],
            quality_result={
                "quality_score": student.get("quality_score", 0),
                "issues": student.get("quality_issues", []),
                "suggestions": student.get("quality_suggestions", [])
            }
        ))
        loop.close()
        
        if result.success:
            student["refinement_suggestions"] = result.output.get("suggestions", [])
            student["needs_regeneration"] = result.output.get("needs_regeneration", False)
            state["messages"].append(f"反馈处理完成: {'; '.join(student['refinement_suggestions'])}")
        else:
            state["errors"].append(f"反馈处理失败: {result.error}")
        
        return state
    
    def _should_regenerate(self, state: AgentState) -> str:
        """判断是否重新生成"""
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        if student.get("needs_regeneration", False) and state["loop_count"] < 3:
            state["messages"].append("质量不达标，准备重新生成视频")
            return "retry"
        
        return "skip"
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """完成当前学生处理"""
        student_id = state["current_student_id"]
        student = state["students"][student_id]
        
        student["status"] = "complete"
        student["complete_time"] = datetime.now().isoformat()
        
        state["messages"].append(f"[{student['topic']}] 处理完成")
        
        # 移动到下一个学生
        state["current_student_index"] += 1
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """判断是否继续处理下一个学生"""
        idx = state["current_student_index"]
        total = state["student_count"]
        
        if idx < total:
            return "next"
        
        state["is_complete"] = True
        state["messages"].append(f"全部完成! 共处理 {total} 个学生")
        return "complete"
    
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行工作流"""
        self.config = config
        
        initial_state = AgentState(
            topic=config.get("topic", ""),
            topics_list=config.get("topics_list", []),
            student_count=config.get("student_count", 1),
            current_student_index=0,
            current_student_id="",
            current_phase="",
            next_action="",
            loop_count=0,
            students={},
            current_result={},
            messages=[],
            errors=[],
            is_complete=False,
            is_error=False
        )
        
        thread_id = str(uuid.uuid4())
        
        final_state = None
        for state in self.graph.stream(initial_state, config={"configurable": {"thread_id": thread_id}}):
            final_state = state
        
        return final_state
    
    def run_stream(self, config: Dict[str, Any]):
        """流式运行，返回每步结果"""
        self.config = config
        
        initial_state = AgentState(
            topic=config.get("topic", ""),
            topics_list=config.get("topics_list", []),
            student_count=config.get("student_count", 1),
            current_student_index=0,
            current_student_id="",
            current_phase="",
            next_action="",
            loop_count=0,
            students={},
            current_result={},
            messages=[],
            errors=[],
            is_complete=False,
            is_error=False
        )
        
        thread_id = str(uuid.uuid4())
        
        for state in self.graph.stream(initial_state, config={"configurable": {"thread_id": thread_id}}):
            yield state


def run_single_student(config: Dict[str, Any]) -> Dict[str, Any]:
    """运行单个学生的工作流（简化版本）"""
    registry = register_all_skills()

    topic = config.get("topic", "General Topic")
    length = config.get("length", 300)
    difficulty = config.get("difficulty", "intermediate")
    style = config.get("style", "general")
    model = config.get("model", "glm")
    tts_method = config.get("tts_method", "piper")
    minimax_voice_id = config.get("minimax_voice_id", "English_Graceful_Lady")
    video_method = config.get("video_method", "wav2lip")
    add_subtitles = config.get("add_subtitles", True)
    soundonly_mode = config.get("soundonly_mode", False)
    wer_threshold = config.get("wer_threshold", 15)
    image_path = config.get("image_path")
    reference_audio = config.get("reference_audio")

    result = {
        "topic": topic,
        "status": "init",
        "messages": []
    }

    # 1. 生成文本
    result["messages"].append("开始生成文本...")
    text_skill = registry.get_skill("generate_text")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    text_result = loop.run_until_complete(text_skill.execute(
        context={},
        topic=topic,
        length=length,
        difficulty=difficulty,
        style=style,
        model=model
    ))
    loop.close()
    
    if not text_result.success:
        result["status"] = "error"
        result["error"] = text_result.error
        return result
    
    result["text"] = text_result.output["text"]
    result["word_count"] = text_result.output.get("word_count", 0)
    result["messages"].append(f"文本生成完成: {result['word_count']}词")
    
    # 2. 选择图片
    if image_path:
        result["image_path"] = image_path
        result["messages"].append(f"使用指定图片: {image_path}")
    else:
        img_skill = registry.get_skill("select_random_image")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        img_result = loop.run_until_complete(img_skill.execute(context={}, prefer_new=True))
        loop.close()
        
        if not img_result.success:
            result["status"] = "error"
            result["error"] = img_result.error
            return result
        
        result["image_path"] = img_result.output["image_path"]
        result["messages"].append(f"随机图片: {result['image_path']}")
    
    # 3. 合成语音
    result["messages"].append("开始语音合成...")
    audio_skill = registry.get_skill("synthesize_speech")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # tts_method: edge/piper/xtts/online/minimax -> 对应到skill的method参数
    audio_result = loop.run_until_complete(audio_skill.execute(
        context={},
        text=result["text"],
        method=tts_method if tts_method != "edge" else "online",  # 转换为skill能识别的method
        reference_audio=reference_audio,
        minimax_voice_id=minimax_voice_id,
        wer_threshold=wer_threshold
    ))
    loop.close()
    
    if not audio_result.success:
        result["status"] = "error"
        result["error"] = audio_result.error
        return result
    
    result["audio_path"] = audio_result.output["audio_path"]
    result["audio_duration"] = audio_result.output.get("duration", 0)
    result["messages"].append(f"语音合成完成: {result['audio_duration']:.1f}秒")
    
    # 4. 生成视频
    result["messages"].append("开始视频生成...")
    video_skill = registry.get_skill("generate_video")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # 只有 SadTalker 支持 fp16 参数，Wav2Lip 不需要
    video_kwargs = {
        "image_path": result["image_path"],
        "audio_path": result["audio_path"],
        "method": video_method
    }
    if video_method == "sadtalker":
        video_kwargs["fp16"] = True  # SadTalker 启用FP16加速
    
    video_result = loop.run_until_complete(video_skill.execute(context={}, **video_kwargs))
    loop.close()
    
    if not video_result.success:
        result["status"] = "error"
        result["error"] = video_result.error
        return result
    
    result["video_path"] = video_result.output["video_path"]
    result["video_duration"] = video_result.output.get("duration", 0)
    result["messages"].append(f"视频生成完成: {result['video_duration']:.1f}秒")
    
    # 5. 质量评估
    result["messages"].append("开始质量评估...")
    eval_skill = registry.get_skill("evaluate_quality")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eval_result = loop.run_until_complete(eval_skill.execute(
        context={},
        video_path=result["video_path"],
        audio_path=result["audio_path"]
    ))
    loop.close()
    
    if eval_result.success:
        result["quality_score"] = eval_result.output.get("quality_score", 0)
        result["quality_issues"] = eval_result.output.get("issues", [])
        result["messages"].append(f"质量评分: {result['quality_score']:.1f}/100")
    else:
        result["quality_score"] = 50
        result["messages"].append("质量评估失败，使用默认分数")
    
    result["status"] = "complete"
    result["complete_time"] = datetime.now().isoformat()
    
    return result


def run_single_student_with_progress(config: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
    """
    运行单个学生的工作流（支持进度回调版本）
    progress_callback: 一个函数，接收 (step, message, progress) 参数
        step: 1=文本, 2=图片, 3=音频, 4=视频, 5=评估
        message: 进度消息
        progress: 0-100的进度值
    """
    registry = register_all_skills()

    topic = config.get("topic", "General Topic")
    length = config.get("length", 300)
    difficulty = config.get("difficulty", "intermediate")
    style = config.get("style", "general")
    model = config.get("model", "glm")
    tts_method = config.get("tts_method", "piper")
    minimax_voice_id = config.get("minimax_voice_id", "English_Graceful_Lady")
    video_method = config.get("video_method", "wav2lip")
    add_subtitles = config.get("add_subtitles", True)
    soundonly_mode = config.get("soundonly_mode", False)
    wer_threshold = config.get("wer_threshold", 15)
    image_path = config.get("image_path")
    reference_audio = config.get("reference_audio")

    result = {
        "topic": topic,
        "status": "init",
        "messages": []
    }

    def send_progress(step, message, progress):
        if progress_callback:
            progress_callback(step, message, progress)

    # 1. 生成文本
    send_progress(1, "开始生成文本...", 10)
    text_skill = registry.get_skill("generate_text")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    text_result = loop.run_until_complete(text_skill.execute(
        context={},
        topic=topic,
        length=length,
        difficulty=difficulty,
        style=style,
        model=model
    ))
    loop.close()
    
    if not text_result.success:
        result["status"] = "error"
        result["error"] = text_result.error
        return result
    
    result["text"] = text_result.output["text"]
    result["word_count"] = text_result.output.get("word_count", 0)
    send_progress(1, f"文本生成完成: {result['word_count']}词", 30)
    
    # 2. 选择图片
    send_progress(2, "开始选择图片...", 35)
    if image_path:
        result["image_path"] = image_path
        send_progress(2, f"使用指定图片: {image_path}", 40)
    else:
        img_skill = registry.get_skill("select_random_image")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        img_result = loop.run_until_complete(img_skill.execute(context={}, prefer_new=True))
        loop.close()
        
        if not img_result.success:
            result["status"] = "error"
            result["error"] = img_result.error
            return result
        
        result["image_path"] = img_result.output["image_path"]
        send_progress(2, f"随机图片: {result['image_path']}", 45)
    
    # 3. 合成语音
    send_progress(3, "开始语音合成...", 50)
    audio_skill = registry.get_skill("synthesize_speech")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_result = loop.run_until_complete(audio_skill.execute(
        context={},
        text=result["text"],
        method=tts_method if tts_method != "edge" else "online",
        reference_audio=reference_audio,
        minimax_voice_id=minimax_voice_id,
        wer_threshold=wer_threshold
    ))
    loop.close()
    
    if not audio_result.success:
        result["status"] = "error"
        result["error"] = audio_result.error
        return result
    
    result["audio_path"] = audio_result.output["audio_path"]
    result["audio_duration"] = audio_result.output.get("duration", 0)
    send_progress(3, f"语音合成完成: {result['audio_duration']:.1f}秒", 60)
    
    # 4. 生成视频
    send_progress(4, "开始视频生成...", 65)
    video_skill = registry.get_skill("generate_video")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    video_kwargs = {
        "image_path": result["image_path"],
        "audio_path": result["audio_path"],
        "method": video_method
    }
    if video_method == "sadtalker":
        video_kwargs["fp16"] = True
    
    video_result = loop.run_until_complete(video_skill.execute(context={}, **video_kwargs))
    loop.close()
    
    if not video_result.success:
        result["status"] = "error"
        result["error"] = video_result.error
        return result
    
    result["video_path"] = video_result.output["video_path"]
    result["video_duration"] = video_result.output.get("duration", 0)
    send_progress(4, f"视频生成完成: {result['video_duration']:.1f}秒", 90)
    
    # 5. 质量评估
    send_progress(5, "开始质量评估...", 92)
    eval_skill = registry.get_skill("evaluate_quality")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eval_result = loop.run_until_complete(eval_skill.execute(
        context={},
        video_path=result["video_path"],
        audio_path=result["audio_path"]
    ))
    loop.close()
    
    if eval_result.success:
        result["quality_score"] = eval_result.output.get("quality_score", 0)
        result["quality_issues"] = eval_result.output.get("issues", [])
        send_progress(5, f"质量评分: {result['quality_score']:.1f}/100", 98)
    else:
        result["quality_score"] = 50
        send_progress(5, "质量评估失败，使用默认分数", 98)
    
    result["status"] = "complete"
    result["complete_time"] = datetime.now().isoformat()
    send_progress(5, "全部完成", 100)
    
    return result


def run_single_student_streaming(config: Dict[str, Any]):
    """
    运行单个学生的工作流（流式版本 - 实时返回SadTalker进度）
    返回一个生成器，每次yield (type, data) 元组
    type: 'progress' | 'complete' | 'error'
    """
    import subprocess
    import threading
    import queue
    
    registry = register_all_skills()
    
    topic = config.get("topic", "General Topic")
    length = config.get("length", 300)
    difficulty = config.get("difficulty", "intermediate")
    style = config.get("style", "general")
    model = config.get("model", "glm")
    tts_method = config.get("tts_method", "piper")
    minimax_voice_id = config.get("minimax_voice_id", "English_Graceful_Lady")
    video_method = config.get("video_method", "wav2lip")
    image_path = config.get("image_path")
    reference_audio = config.get("reference_audio")

    result = {
        "topic": topic,
        "status": "init",
        "messages": []
    }

    # 1. 生成文本
    yield ('progress', {'step': 1, 'message': '开始生成文本...', 'progress': 10})
    text_skill = registry.get_skill("generate_text")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    text_result = loop.run_until_complete(text_skill.execute(
        context={},
        topic=topic,
        length=length,
        difficulty=difficulty,
        style=style,
        model=model
    ))
    loop.close()
    
    if not text_result.success:
        yield ('error', {'error': text_result.error})
        return
    
    result["text"] = text_result.output["text"]
    result["word_count"] = text_result.output.get("word_count", 0)
    yield ('progress', {'step': 1, 'message': f'文本生成完成: {result["word_count"]}词', 'progress': 30})
    
    # 2. 选择图片
    yield ('progress', {'step': 2, 'message': '开始选择图片...', 'progress': 35})
    if image_path:
        result["image_path"] = image_path
        yield ('progress', {'step': 2, 'message': f'使用指定图片: {image_path}', 'progress': 40})
    else:
        img_skill = registry.get_skill("select_random_image")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        img_result = loop.run_until_complete(img_skill.execute(context={}, prefer_new=True))
        loop.close()
        
        if not img_result.success:
            yield ('error', {'error': img_result.error})
            return
        
        result["image_path"] = img_result.output["image_path"]
        yield ('progress', {'step': 2, 'message': f'随机图片: {result["image_path"]}', 'progress': 45})
    
    # 3. 合成语音
    yield ('progress', {'step': 3, 'message': '开始语音合成...', 'progress': 50})
    audio_skill = registry.get_skill("synthesize_speech")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_result = loop.run_until_complete(audio_skill.execute(
        context={},
        text=result["text"],
        method=tts_method if tts_method != "edge" else "online",
        reference_audio=reference_audio,
        minimax_voice_id=minimax_voice_id
    ))
    loop.close()
    
    if not audio_result.success:
        yield ('error', {'error': audio_result.error})
        return
    
    result["audio_path"] = audio_result.output["audio_path"]
    result["audio_duration"] = audio_result.output.get("duration", 0)
    yield ('progress', {'step': 3, 'message': f'语音合成完成: {result["audio_duration"]:.1f}秒', 'progress': 60})
    
    # 4. 生成视频（流式 - 实时返回SadTalker输出）
    yield ('progress', {'step': 4, 'message': '开始视频生成...', 'progress': 65})
    
    if video_method == "sadtalker":
        # SadTalker流式版本 - 直接调用子进程并实时返回输出
        from config import SADTALKER_PY, SADTALKER_MODEL_PATH
        from pathlib import Path
        
        sadtalker_dir = Path(SADTALKER_MODEL_PATH)  # D:\_BiShe\sadtalker
        inference_script = sadtalker_dir / "inference.py"
        
        # 构建命令（🚀 优化版）
        cmd = [
            str(SADTALKER_PY), str(inference_script),
            "--driven_audio", str(result["audio_path"]),
            "--source_image", str(result["image_path"]),
            "--result_dir", str(sadtalker_dir / "output"),
            "--expression_scale", "1.0",
            "--size", "512",
            "--batch_size", "4",       # 🚀 提升并行处理能力
            # 不传 --enhancer 参数，使用默认值 None（禁用GFPGAN）
            "--fp16"                   # 🚀 现在真正生效（已修改代码）
        ]
        
        # 设置环境
        import os
        env = os.environ.copy()
        env['CUDA_LAUNCH_BLOCKING'] = '1'
        env['TORCH_CUDNN_V8_API_ENABLED'] = '1'
        
        yield ('progress', {'step': 4, 'message': 'SadTalker 启动...', 'progress': 68, 'raw_output': True})
        
        print(f"[SadTalker] 开始生成视频...")
        
        # 启动子进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(sadtalker_dir),
            env=env
        )
        
        # 使用队列在线程间传递
        output_queue = queue.Queue()
        
        def read_stdout():
            for line in process.stdout:
                line = line.rstrip('\n')
                if line:
                    print(f"[SadTalker] {line}")  # 打印到服务器终端
                    output_queue.put(('stdout', line))
        
        def read_stderr():
            for line in process.stderr:
                line = line.rstrip('\n')
                if line:
                    print(f"[SadTalker Error] {line}")  # 打印到服务器终端
                    output_queue.put(('stderr', line))
        
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
        
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        
        # 检查结果
        if process.returncode != 0:
            yield ('error', {'error': 'SadTalker 执行失败'})
            return
        
        # 获取输出视频路径
        output_dir = sadtalker_dir / "output"
        video_files = list(output_dir.glob("*.mp4")) + list(output_dir.glob("*.webm"))
        if video_files:
            # 获取最新的视频文件
            latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
            result["video_path"] = str(latest_video)
        else:
            yield ('error', {'error': '未找到生成的视频文件'})
            return
            
    else:
        # Wav2Lip版本（非流式）
        video_skill = registry.get_skill("generate_video")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        video_result = loop.run_until_complete(video_skill.execute(
            context={},
            image_path=result["image_path"],
            audio_path=result["audio_path"],
            method=video_method
        ))
        loop.close()
        
        if not video_result.success:
            yield ('error', {'error': video_result.error})
            return
        
        result["video_path"] = video_result.output["video_path"]
        result["video_duration"] = video_result.output.get("duration", 0)
    
    yield ('progress', {'step': 4, 'message': f'视频生成完成', 'progress': 90})
    
    # 5. 质量评估
    yield ('progress', {'step': 5, 'message': '开始质量评估...', 'progress': 92})
    eval_skill = registry.get_skill("evaluate_quality")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eval_result = loop.run_until_complete(eval_skill.execute(
        context={},
        video_path=result["video_path"],
        audio_path=result["audio_path"]
    ))
    loop.close()
    
    if eval_result.success:
        result["quality_score"] = eval_result.output.get("quality_score", 0)
        result["quality_issues"] = eval_result.output.get("issues", [])
        yield ('progress', {'step': 5, 'message': f'质量评分: {result["quality_score"]:.1f}/100', 'progress': 98})
    else:
        result["quality_score"] = 50
        yield ('progress', {'step': 5, 'message': '质量评估失败，使用默认分数', 'progress': 98})
    
    result["status"] = "complete"
    result["complete_time"] = datetime.now().isoformat()
    yield ('complete', result)
