# AI Agent 全自动英语演讲视频生成系统

## 系统概述

本系统基于 LangGraph 的 ReAct（Reasoning + Acting）模式，实现了从用户自然语言需求到完整视频生成的全自动流程。

## 核心改进

### 1. 真正的 ReAct Agent
- **之前**: 只能对话和提取参数，无法自动执行
- **现在**: AI Agent 会自动调用工具链，从文本生成到视频制作一气呵成

### 2. 智能默认值
当用户没有指定某些参数时，系统使用智能默认值：
- **难度**: college_cet（大学四六级水平）
- **风格**: informative（信息型）
- **主播**: 女性、年轻成人、开心表情
- **字数**: 300词
- **背景**: 办公室

### 3. 自动执行流程
用户只需说"帮我制作一个关于气候变化的英语演讲视频"，AI Agent 会：
1. 理解主题：气候变化
2. 生成英文演讲稿
3. 选择人物头像
4. 语音合成
5. 生成说话视频
6. 评估质量
7. 向用户报告结果

## 如何使用

### 方式一：Web 界面（推荐）

1. 启动服务器：
```bash
cd D:\_BiShe\demo_1
python server.py
```

2. 访问 AI Agent 界面：
- 完整界面：http://localhost:5000/frontend
- 专用 Agent 界面：http://localhost:5000/agent（推荐）

3. 与 AI 对话：
- ✅ "帮我制作一个关于环保的英语演讲视频"
- ✅ "生成10个关于科技的话题"
- ✅ "做一个商业演讲的视频"

### 方式二：API 调用

```python
import requests

# 调用 Agent 聊天
response = requests.post('http://localhost:5000/api/agent/chat', json={
    'message': '帮我制作一个关于气候变化的英语演讲视频',
    'history': [],
    'auto_execute': False  # 或 True 自动执行
})

result = response.json()
print(result['response'])  # AI 的回复
print(result['config'])      # 提取的配置
print(result['execution_history'])  # 执行的历史
```

### 方式三：流式输出

```python
import requests

response = requests.post('http://localhost:5000/api/agent/fullauto/stream', 
    json={'message': '帮我制作一个关于环保的视频'},
    stream=True)

for line in response.iter_lines():
    if line.startswith('data: '):
        data = json.loads(line[6:])
        print(data['type'], data)
```

## API 接口

### 1. `/api/agent/chat` - 聊天接口（ReAct模式）
- 输入：用户消息 + 历史记录
- 输出：AI 回复 + 配置参数 + 执行历史

### 2. `/api/agent/fullauto` - 全自动模式
- 自动执行完整的视频生成流程

### 3. `/api/agent/fullauto/stream` - 流式全自动
- 实时返回每个执行步骤

### 4. `/api/agent/execute` - 执行生成
- 根据配置参数执行视频生成

## 工作流程

```
用户输入
    ↓
ReAct Agent 理解需求
    ↓
提取/设置配置参数
    ↓
┌──────────────────────────────────────┐
│  步骤1: generate_english_speech      │
│  生成英文演讲稿                        │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  步骤2: select_character_image       │
│  选择人物头像                          │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  步骤3: synthesize_speech            │
│  语音合成                             │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  步骤4: generate_talking_video      │
│  生成说话视频                          │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  步骤5: evaluate_video_quality      │
│  质量评估                             │
└──────────────────────────────────────┘
    ↓
向用户报告结果
```

## 注意事项

1. **首次使用**: 系统会使用默认参数，用户无需指定所有细节
2. **批量生成**: 可以说"生成10个视频"，系统会自动生成不同主题
3. **实时反馈**: Agent 会实时报告每个步骤的执行结果
4. **错误处理**: 如果某一步失败，Agent 会尝试解释原因并建议解决方案

## 技术亮点

- **LangGraph**: 构建 ReAct 工作流
- **多工具集成**: 与现有的 skills.py 无缝集成
- **流式输出**: 实时显示执行进度
- **记忆管理**: 支持多轮对话上下文

## 文件清单

- `ai_agent.py`: ReAct Agent 核心模块（新增）
- `server.py`: 后端服务器（已更新）
- `frontend/agent.html`: 专用 Agent 界面（新增）
- `frontend/index.html`: 完整界面（已更新）
- `skills.py`: 技能库（保持不变）
- `workflow.py`: 工作流（保持不变）

## 示例对话

### 示例1：简单需求
**用户**: 帮我制作一个关于环保的英语演讲视频

**Agent**: 
- 调用 generate_english_speech(topic="环保")
- 调用 select_character_image()
- 调用 synthesize_speech()
- 调用 generate_talking_video()
- 调用 evaluate_video_quality()
- 返回：视频生成完成！🎉

### 示例2：详细需求
**用户**: 生成一个300词的大学四六级水平的商业演讲视频，男性主播

**Agent**:
- 理解参数：topic=商业演讲, length=300, difficulty=college_cet, image_gender=male
- 执行工作流
- 返回：视频生成完成！

### 示例3：批量生成
**用户**: 我想生成10个关于人工智能的英语演讲视频

**Agent**:
- 理解：批量生成10个视频
- 执行10次完整工作流
- 返回：10个视频全部生成完成！📦

## 常见问题

**Q: 为什么 Agent 不询问更多参数？**
A: 系统使用智能默认值，当信息足够时立即开始执行，避免反复询问。

**Q: 如何修改默认参数？**
A: 在 ai_agent.py 的 _get_system_prompt() 方法中修改默认值设置。

**Q: Agent 失败了怎么办？**
A: 查看执行历史（execution_history）了解哪一步失败，Agent 通常会提供错误原因。

**Q: 如何查看生成的视频？**
A: 在 Web 界面右侧会显示预览，也可以通过 agent_result_actions 打开文件夹。

## 未来扩展

- 支持更多视频风格
- 添加字幕自动生成
- 集成更先进的语音克隆
- 支持批量自定义参数
