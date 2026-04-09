"""
文本生成/读取模块
支持三种模式:
1. 用户给定完整文本
2. AI根据主题和长度要求生成文本
3. 随机生成日常演讲/口语练习文本
"""
import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class SpeechRequest:
    """演讲请求数据结构"""
    mode: str  # "user_text", "ai_generate", "random"
    content: Optional[str] = None  # 用户提供的文本 (mode=user_text)
    topic: Optional[str] = None  # 演讲主题 (mode=ai_generate)
    length: Optional[int] = None  # 期望字数 (mode=ai_generate/random)
    difficulty: Optional[str] = "intermediate"  # easy/intermediate/advanced
    style: Optional[str] = "general"  # general/business/academic/casual


class TextProvider(ABC):
    """文本提供者抽象基类"""
    
    @abstractmethod
    def generate(self, request: SpeechRequest) -> str:
        pass


class UserTextProvider(TextProvider):
    """用户直接提供文本"""
    
    def generate(self, request: SpeechRequest) -> str:
        if not request.content:
            raise ValueError("用户模式需要提供content参数")
        return request.content


class AIGenerateProvider(TextProvider):
    """AI根据要求生成文本"""
    
    def __init__(self, api_config: Dict[str, Any]):
        self.api_config = api_config
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            provider = self.api_config.get("provider", "openai")
            if provider in ("openai", "minimax"):
                try:
                    from openai import OpenAI
                    cfg = self.api_config
                    self._client = OpenAI(
                        api_key=cfg.get("api_key", ""),
                        base_url=cfg.get("base_url")
                    )
                except ImportError:
                    raise ImportError("请安装openai包: pip install openai")
            elif provider == "anthropic":
                try:
                    from anthropic import Anthropic
                    self._client = Anthropic(api_key=self.api_config.get("api_key", ""))
                except ImportError:
                    raise ImportError("请安装anthropic包: pip install anthropic")
            elif provider == "local":
                try:
                    import ollama
                    self._client = ollama
                except ImportError:
                    raise ImportError("请安装ollama包: pip install ollama")
        return self._client
    
    def generate(self, request: SpeechRequest) -> str:
        if not request.topic:
            raise ValueError("AI生成模式需要提供topic参数")
        
        length = request.length or 300
        difficulty = request.difficulty or "intermediate"
        style = request.style or "general"
        
        prompt = self._build_prompt(request.topic, length, difficulty, style)
        
        provider = self.api_config.get("provider", "openai")
        
        if provider in ("openai", "minimax", "glm", "anthropic"):
            return self._generate_from_api(prompt)
        elif provider == "local":
            return self._generate_from_local(prompt)
        else:
            raise ValueError(f"不支持的provider: {provider}")
    
    def _build_prompt(self, topic: str, length: int, difficulty: str, style: str) -> str:
        # 难度级别描述 - 每种约80-120词
        difficulty_desc = {
            "elementary": """小学水平英语演讲 - 适合英语初学者。使用最常用的500个以内单词，避免生僻词。句子简单，8-12词，主谓宾基本句型。不使用从句。话题限于日常熟悉领域：家庭、学校、朋友、爱好等。时态以一般现在时为主。风格童趣自然，像孩子分享小世界。适合小学课堂或初学者交流活动。""",
            
            "middle_school": """初中水平英语演讲 - 适合具备初步英语表达能力的学习者。词汇覆盖初中1500核心词汇。句子12-18词，可用because、when、if等简单从句。内容涉及校园生活、兴趣爱好、节日习俗等。可使用比较级、现在完成时、一般将来时。风格轻松易懂，逻辑清晰。适合初中生课堂演讲或社团活动。""",
            
            "high_school": """高中水平英语演讲 - 适合具备较好英语基础的学习者。词汇达高考3500词范围。句子15-25词，复杂句式占40%以上。需熟练运用多种从句（名词性从句、定语从句、状语从句）和非谓语动词。可探讨社会现象、科技发展等深度话题。语法完整，能用虚拟语气和倒装句。风格成熟稳重、论证有力。适合演讲比赛或面试使用。""",
            
            "college_cet": """大学四六级水平英语演讲 - 适合四六级考生或相当水平学习者。词汇达四六级5000-6000词。句子20-30词，复杂句超50%。能用各种从句和虚拟语气、倒装句、强调句型等高级语法。可探讨教育公平、职业规划、科技伦理等思辨性议题。风格逻辑清晰、论证深入、用词精准。适合演讲比赛或学术研讨会。""",
            
            "english_major": """英语专业水平英语演讲 - 适合英语专业学生或高级英语使用者。词汇达专八10000-12000词。句子复杂多变，长短交错。可准确运用所有从句类型和高级语法结构（独立主格、With复合结构等）。内容可深入探讨人文学科或前沿科技话题。大量运用高端修辞（隐喻、讽喻、头韵等）。风格博学深邃、语言优美。适合专业演讲比赛或学术会议。""",
            
            "native": """母语级英语演讲 - 适合期望达到接近母语水平的高级英语使用者。词汇12000词以上，运用最精确地道的英语表达。句子结构完全自由，长短变化无穷。能娴熟运用所有语法结构。内容可发表深刻见解，涵盖专业学术、社会争议、哲学思考等。修辞手法出神入化。风格浑然天成、圆融自如、魅力四射。适合国际会议或TED级别演讲。"""
        }
        
        # 演讲风格描述 - 每种约80-120词
        style_desc = {
            "motivational": """激励型演讲 - 目标：激发听众热情与行动力。开场用惊人数据、感人故事或提问抓住注意力。主体层层递进：建立共鸣→指出问题→提出方案→发出行动号召。大量使用排比句增强气势。讲述成功案例证明目标可达。结尾铿锵有力，用重复和押韵创造记忆点。节奏较快，高潮迭起，听众情绪起伏，最终带着正能量离开。""",
            
            "persuasive": """说服型演讲 - 目标：让听众接受特定观点或采取行动。首先建立可信度和亲和力。清晰陈述核心观点，提供事实依据、数据支撑、专家引用。运用演绎法、归纳法、类比法、对比法等多种论证。预判反方意见并回应。情感与逻辑结合，但不过度情绪化。结构：引言提出观点-主体论证-结尾总结发出行动号召。语言精确有力，避免模糊词汇。""",
            
            "informative": """信息型演讲 - 目标：清晰传递知识，让听众有新系统理解。评估听众现有知识水平，决定内容深度。按逻辑顺序组织信息：时间顺序、空间顺序或重要程度顺序。每个观点有清晰解释和充分例子，用类比将复杂概念简单化。每隔一段时间进行小结，避免信息过载，聚焦3-5个核心要点。结尾总结关键信息，提供进一步学习资源。语言清晰准确、条理分明。""",
            
            "entertaining": """娱乐型演讲 - 目标：在轻松愉快氛围中传递信息，让听众在欢笑中获得启发。具备幽默感，自我调侃，观察生活荒诞处并巧妙呈现。开场创造轻松氛围，但娱乐性不等于浅薄，幽默服务核心信息。结构可相对松散但有隐藏逻辑主线。使用夸张、反讽、意外转折等喜剧技巧。语言口语化、自然流畅，可设置"抖包袱"节奏。亲切近人，听众放松状态下接受信息。""",
            
            "ceremonial": """仪式型演讲 - 在正式庄重场合进行，庆祝重要时刻或纪念特殊人物。场合包括颁奖典礼、开幕式、毕业典礼、就职仪式、纪念活动等。语言正式典雅，符合场合庄重感，避免幽默或轻浮表达。情感真挚但克制有力。开场点明仪式主题，主体回顾成就或阐述愿景，结尾将情感推向高潮。用排比句和庄严韵律增强力量，可引用名言诗歌增加文采。风格简洁有力、情感饱满、令人难忘。""",
            
            "keynote": """主题型演讲 - 在大型会议或论坛就重大议题发表深刻见解，启发思考、引领方向。演讲者是领域权威或思想领袖，提供独特视角和前瞻洞见。选题有高度和广度，涉及根本性问题。内容有深度，提供深思熟虑的见解。开篇用震惊数据或深刻洞察抓住注意力。主体系统展开观点，借用历史典故、哲学思想丰富论述。鼓励听众挑战思维定式。结尾有力而开放，为未来思考留下空间。风格严肃深刻但不晦涩。""",
            
            "demonstration": """展示型演讲 - 目标：通过演示教给听众某种技能或操作方法。开篇明确告诉听众将学到什么、学成后能做什么，激发学习动机。演示分解成清晰步骤，每步解释做什么和为什么。展示实物关键特征和使用方法。使用"之前/之后"对比。适当放慢速度确保听众跟上，关键处停顿或重复。把专业术语转化为日常语言，用熟悉事物解释陌生概念。结尾总结关键步骤，提醒常见错误，给出练习建议。风格实用导向、条理清晰。""",
            
            "tributary": """致敬型演讲 - 目的：赞美表彰某人或团体的成就、品质或贡献，表达深深敬意。场合包括颁奖典礼、纪念活动、告别演说、追悼会等。搜集呈现被致敬者的生平事迹、主要成就、优秀品质。通过具体故事展现人格魅力，避免空洞溢美之词。在个人特质和更广泛意义间建立联系，让致敬既具体又升华。情感真挚深沉但优雅得体，不过于煽情。语言有文采，用比喻、排比增强感染力。结尾将敬意推向高潮。风格共鸣性强，让精神和成就得以传承。""",
            
            "controversial": """争议型演讲 - 就争议性话题提出独特激进观点，引发思考和讨论。论点有理有据、论据确凿、论证严密，让反对者也无法轻易驳斥。充分准备反方观点并逐一回应，承认合理处但指出局限性。语言有锋芒力量，不畏惧冲突但保持对听众的尊重。开场直接挑战主流观点，让听众意识到不同寻常。主体剥离问题表面深入核心，展示观点独特价值。结尾开放问题，邀请继续思考，保持争议热度。风格锐利勇敢、逻辑缜密，激励独立思考。""",
            
            "storytelling": """故事型演讲 - 通过连贯故事传递道理、表达情感或启发行动。故事比逻辑论证更能打动人心、留下深刻记忆。故事可以是亲身经历、他人故事、历史典故或虚构情节，但必须服务核心主题。讲述注重细节丰富性：场景、人物外貌、对话、情绪变化等。故事有清晰叙事线：起始状态-冲突/转折-解决-结局。适当制造悬念，在结尾揭示道理但自然流出。设置情感曲线让听众情绪起伏。语言生动具体，多用感官词汇。结尾回扣主题升华意义。风格引人入胜、情感丰富、富有感染力。"""
        }
        
        return f"""请生成一篇约{length}词的全英文演讲稿。

【演讲信息】
主题: {topic}
目标词数: {length}词
英语能力等级: {difficulty_desc.get(difficulty, difficulty_desc['college_cet'])}
演讲风格: {style_desc.get(style, style_desc['informative'])}

【写作要求】
1. 演讲稿必须全部是英文
2. 严格按照目标词数{length}词生成（允许±10词误差）
3. 结构清晰：引言(10%)、主体(75%)、结语(15%)
4. 适合口头演讲，节奏感强
5. 不需要包含演讲者名字或标题，直接输出正文
6. 段落之间用空行分隔
7. 【重要】请选择一个独特的切入角度，避免与常见演讲雷同

请直接输出演讲稿正文（必须达到约{length}词）:"""

    def _generate_from_api(self, prompt: str) -> str:
        provider = self.api_config.get("provider", "openai")
        base_url = self.api_config.get("base_url", "")
        
        try:
            if provider in ("minimax", "glm") and ("minimax.chat" in base_url or "bigmodel.cn" in base_url):
                # MiniMax/GLM OpenAI兼容模式 - 使用 OpenAI SDK
                from openai import OpenAI
                client = OpenAI(
                    api_key=self.api_config.get("api_key", ""),
                    base_url=base_url
                )
                response = client.chat.completions.create(
                    model=self.api_config.get("model", "MiniMax-M2.7"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=3000,
                    timeout=600
                )
                content = response.choices[0].message.content.strip()
                if not content:
                    raise RuntimeError(f"{provider} API 返回内容为空")
                return content
                
            elif provider == "openai":
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.api_config.get("model", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=60
                )
                return response.choices[0].message.content.strip()
            elif provider == "anthropic":
                client = self._get_client()
                response = client.messages.create(
                    model=self.api_config.get("model", "claude-3-haiku"),
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=60
                )
                return response.content[0].text.strip()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")
    
    def _extract_final_answer(self, reasoning: str) -> str:
        """从 MiniMax 的 reasoning_content 中提取最终回复"""
        import re
        # 移除思考过程标记
        reasoning = reasoning.strip()
        
        # MiniMax M2.7 的 reasoning_content 通常以 "think" 开头，后面跟着实际回复
        # 我们需要找到实际回复内容的开始位置
        
        # 方法1: 去掉 "think\n" 前缀
        if reasoning.startswith("think\n"):
            reasoning = reasoning[6:]
        
        # 方法2: 查找 "Here is" 或 "Now" 等实际回复开始的标记
        patterns_to_skip = [
            r'^The user wants',
            r'^We need to',
            r'^We must',
            r'^We should',
            r'^Now we need',
            r'^Now count',
            r'^Word count',
            r'^Let us',
            r'^First,? we',
            r'^Let\'s? (count|write|produce)',
            r'^We\'ll (count|write|produce)',
            r'^This (speech|text|response)',
            r'^The (speech|text|response)',
            r'^Here(\'s| is) (the |a )',
        ]
        
        lines = reasoning.split('\n')
        content_lines = []
        skip_mode = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是思考过程行
            is_thinking = False
            for pattern in patterns_to_skip:
                if re.match(pattern, line, re.IGNORECASE):
                    is_thinking = True
                    break
            
            # 跳过包含计数/思考关键词的行
            thinking_keywords = ['We must', 'We need', 'Let us', 'Thus', 'Therefore', 
                               'In conclusion', 'We should', 'Now count', 'Word count', 
                               'Let\'s count', 'Let me count', 'maybe', 'perhaps', 
                               'possibly', 'probably', 'This is', 'It is a',
                               'The user', 'We can']
            if any(line.startswith(kw) for kw in thinking_keywords):
                is_thinking = True
            
            if is_thinking:
                skip_mode = True
                continue
            
            # 正常内容行
            if line and not skip_mode:
                content_lines.append(line)
            elif line and skip_mode and len(content_lines) > 0:
                # 如果之前跳过了但现在找到了正常内容，可能是回复开始了
                skip_mode = False
                content_lines.append(line)
        
        if content_lines:
            # 返回合并的内容
            result = ' '.join(content_lines)
            # 清理可能的引号
            result = re.sub(r'^["\']|["\']$', '', result)
            return result.strip()
        
        # 方法3: 如果以上都失败，尝试找最后一个完整句子
        sentences = re.split(r'(?<=[.!?])\s+', reasoning)
        if sentences:
            # 跳过太短的句子
            for sent in reversed(sentences):
                if len(sent) > 50:  # 正常回复句子应该比较长
                    return sent.strip()
        
        return reasoning
    
    def _generate_from_local(self, prompt: str) -> str:
        client = self._get_client()
        try:
            response = client.chat(model=self.api_config.get("model", "llama3"), messages=[
                {"role": "user", "content": prompt}
            ])
            return response['message']['content'].strip()
        except Exception as e:
            raise RuntimeError(f"本地模型调用失败: {str(e)}")


class RandomSpeechProvider(TextProvider):
    """随机生成日常演讲/口语练习文本"""
    
    TOPICS = [
        "daily routines and productivity tips",
        "favorite books and recommendations",
        "travel experiences and destinations",
        "technology trends and their impact",
        "health and wellness habits",
        "environmental protection actions",
        "cultural differences and similarities",
        "childhood memories and lessons",
        "future career aspirations",
        "hobbies and personal interests"
    ]
    
    OPENERS = [
        "Today, I'd like to share some thoughts about",
        "In this speech, I'll be discussing",
        "Let me tell you about",
        "I'd like to talk about",
        "This presentation will focus on",
        "Allow me to share my perspective on"
    ]
    
    def generate(self, request: SpeechRequest) -> str:
        topic = request.topic or random.choice(self.TOPICS)
        target_length = request.length or 300
        difficulty = request.difficulty or "intermediate"
        
        # 根据难度和目标长度选择模板
        if difficulty == "easy":
            template = self._easy_template(topic)
        elif difficulty == "advanced":
            template = self._advanced_template(topic)
        else:
            template = self._intermediate_template(topic)
        
        # 如果目标长度与模板长度差异较大，尝试调整
        word_count = len(template.split())
        if abs(word_count - target_length) > 50:
            # 如果差异较大，添加或删除句子来接近目标长度
            template = self._adjust_length(template, target_length)
        
        return template
    
    def _adjust_length(self, template: str, target_length: int) -> str:
        """根据目标长度调整文本"""
        words = template.split()
        current_length = len(words)
        
        # 简单策略：复制或删除段落来调整长度
        paragraphs = template.split('\n\n')
        
        if current_length < target_length and paragraphs:
            # 需要增加内容 - 重复最后一段
            needed = target_length - current_length
            last_para = paragraphs[-1]
            # 添加句子来增加长度
            additional = []
            sentences = last_para.split('. ')
            for i in range(min(3, len(sentences))):
                if sum(len(s.split()) for s in additional) < needed:
                    additional.append(sentences[i % len(sentences)] + '.')
            if additional:
                paragraphs.append(' '.join(additional))
                template = '\n\n'.join(paragraphs)
        
        return template
    
    def _easy_template(self, topic: str) -> str:
        opener = random.choice(self.OPENERS)
        return f"""{opener} {topic}.

First, let me start by saying that this topic is very important to many people. 

I think we can all agree that {topic} affects our daily lives in many ways. 

There are a few key points I would like to make. 

First, it helps us understand things better. 

Second, it makes our life more interesting. 

Third, we can learn a lot from it.

In conclusion, I hope you found this information useful. 

Thank you for listening to my speech about {topic}."""

    def _intermediate_template(self, topic: str) -> str:
        opener = random.choice(self.OPENERS)
        return f"""{opener} {topic}.

In today's presentation, I will explore several key aspects of {topic}. This is a topic that impacts many of us in our daily lives, and understanding it better can help us make more informed decisions.

Let me start by providing some background. Many experts believe that {topic} plays a crucial role in our modern society. Over the past few years, we have seen significant changes in how this area develops and evolves.

There are three main points I would like to discuss today. First, we need to understand the basic concepts and principles. Second, we should consider the practical applications and real-world examples. Third, let me share some tips and recommendations that you can apply in your own life.

To illustrate my points, I would like to share a personal experience. When I first became interested in {topic}, I realized that it was more complex than I had initially thought. However, with time and practice, I was able to develop a deeper understanding.

In summary, {topic} is an important subject that deserves our attention. I hope this presentation has provided you with valuable insights and practical knowledge.

Thank you very much for your attention. I would be happy to answer any questions you might have."""

    def _advanced_template(self, topic: str) -> str:
        opener = random.choice(self.OPENERS)
        return f"""{opener} {topic}.

The significance of {topic} cannot be overstated in contemporary discourse. As we navigate the complexities of the modern world, understanding this multifaceted subject becomes increasingly essential for personal and professional development.

To begin with, let us examine the historical context and theoretical foundations that underpin our current understanding of {topic}. Scholars and practitioners alike have long recognized its profound implications across various domains of human endeavor.

I propose to divide our exploration into three interconnected segments. Initially, we shall delve into the fundamental principles and conceptual frameworks that govern this domain. Subsequently, we will examine empirical evidence and case studies that illuminate its practical manifestations. Finally, I will present innovative approaches and forward-looking perspectives that may shape future developments.

It is worth noting that my own journey with {topic} has been transformative. What initially appeared as a formidable challenge gradually revealed itself as an opportunity for substantial growth and insight. This personal evolution exemplifies the broader potential that lies within each of us to master such subjects.

Furthermore, the interdisciplinary nature of {topic} demands that we adopt a holistic perspective. By synthesizing insights from multiple fields and integrating diverse methodologies, we can achieve a more comprehensive and nuanced comprehension.

In conclusion, I would like to leave you with several key takeaways. First, {topic} represents a critical area of inquiry with far-reaching consequences. Second, continued learning and adaptability are essential for navigating this evolving landscape. Third, the practical applications of this knowledge extend well beyond theoretical understanding.

I trust that this presentation has enriched your perspective on {topic} and inspired further exploration. I welcome your questions and look forward to continued dialogue on this compelling subject."""


class TextManager:
    """文本管理器 - 统一接口"""
    
    def __init__(self, api_config: Dict[str, Any]):
        self.providers = {
            "user_text": UserTextProvider(),
            "ai_generate": AIGenerateProvider(api_config),
            "random": RandomSpeechProvider()
        }
    
    def get_text(self, request: SpeechRequest) -> str:
        """
        获取演讲文本
        
        Args:
            request: SpeechRequest对象
            
        Returns:
            str: 处理后的文本
        """
        provider = self.providers.get(request.mode)
        if not provider:
            raise ValueError(f"未知模式: {request.mode}")
        
        text = provider.generate(request)
        
        # 基础文本清理
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        return text.strip()
    
    def save_text(self, text: str, filename: str) -> str:
        """保存文本到文件"""
        from config import OUTPUT_DIR
        output_dir = OUTPUT_DIR / "text"
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return str(filepath)
    
    def load_text(self, filepath: str) -> str:
        """从文件读取文本"""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
