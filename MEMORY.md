# 项目记忆 - AI 英语演讲视频生成系统

## 重要代码修改记录

### 1. 文本生成提示词模板 (models/text/__init__.py)
**修改内容**: 添加了"独特角度"指令，确保批量生成时每个视频内容不同

```
原提示词可能产生相同内容...
现提示词强调: "请从一个独特、有趣的角度切入，避免泛泛而谈..."
```

### 2. 随机主题批量生成 (agent_workflow.py)
**修改内容**: 批量模式下预先生成不同的随机主题

```
批量模式逻辑:
- 手动输入模式: topic_mode='manual', 相同主题但不同角度
- 随机模式: topic_mode='random', 为每个视频生成不同随机主题
```

### 3. 图片库功能 (skills.py)
**修改位置**: `ImageLibrary` 类
**功能**: 从 `image_library/` 文件夹随机选择头像图片

```
image_library/ 结构:
- female_1.jpg, male_1.jpg, male_2.jpg (示例图片)
- 可添加任意数量图片，系统会随机选择
```

### 4. API配置修改 (api_config.py)
**当前配置**:
```python
API_CONFIG = {
    "text_api": {
        "provider": "glm",        # 使用GLM免费模型
        "api_key": "你的GLM密钥",
        "model": "glm-4-flash-250414",
        "base_url": "https://open.bigmodel.cn/api/paas/v4"
    },
    "tts_api": {
        "provider": "minimax",
        "api_key": "你的MiniMax密钥",
        "model": "speech-2.8-hd"
    },
    "image_api": {
        "provider": "minimax",
        "api_key": "你的MiniMax密钥",
        "model": "image-01"
    }
}
```

### 5. 前端标签页结构 (frontend/index.html)
```
三个标签页:
1. tab_agent   -> AI Agent模式 (自然语言交互)
2. tab_custom  -> 定制模式 (手动配置)
3. tab_batch   -> 批量模式 (批量生成)

关键DOM元素:
- state.config.length         # 文本长度滑块值
- agentMode (已移除， legacy代码导致错误)
```

### 6. 已修复的Bug

| Bug | 修复方式 |
|-----|----------|
| AI Agent聊天返回"'minimax'"错误 | 改用 `API_CONFIG['text_api']` (GLM模型) |
| 图片库显示数量不正确 | 移除 `agentMode.forEach` 错误代码 |
| 批量模式滑块值总显示300 | 添加 `state.config.length = parseInt(e.target.value)` |
| 文件夹打开路径错误 | 改用 `explorer "{path}"` 直接打开文件夹 |

## API接口一览

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/generate` | POST | 启动完整工作流 |
| `/api/agent/chat` | POST | AI Agent聊天 (使用text_api) |
| `/api/agent/generate` | POST | 批量生成 |
| `/api/agent/image_library` | GET | 获取图片库信息 |
| `/api/open_folder` | POST | 打开文件夹 |
| `/api/text/generate` | POST | 仅生成文本 |
| `/api/tts/synthesize` | POST | 仅合成语音 |
| `/api/image/process` | POST | 处理图像 |
| `/api/video/generate` | POST | 生成视频 |
| `/api/upload_captured_image` | POST | 上传拍摄图片 |

## 工作流类

| 类 | 文件 | 用途 |
|----|------|------|
| `SpeechVideoWorkflow` | workflow.py | 手动/半自动模式核心类 |
| `AgentWorkflow` | agent_workflow.py | Agent/批量模式核心类 |
| `run_single_student()` | agent_workflow.py | 单个学生视频生成 |
| `SkillsRegistry` | skills.py | 技能注册表 |
| `Skill` | skills.py | 技能基类 |
| `ImageLibrary` | skills.py | 本地图片库技能 |

## 启动方式

```bash
# 方式1: 启动API服务器
python server.py
# 访问 http://localhost:5000/frontend

# 方式2: 直接运行
python main.py
```

## 外部依赖路径

| 模型 | 路径 |
|------|------|
| Piper TTS | `D:\_BiShe\piper-tts\` |
| XTTS V2 | `D:\_BiShe\xtts-v2\` |
| Faster Whisper | `D:\_BiShe\faster-whisper\` |
| Wav2Lip | `D:\_BiShe\wav2lip\` |
| SadTalker | `D:\_BiShe\sadtalker\` |
| GFPGAN | `D:\_BiShe\gfpgan\` |

## 前端状态管理

```javascript
const state = {
    currentTab: 'agent',
    config: {
        length: 300,           // 文本长度
        topic: '',
        difficulty: 'intermediate',
        style: 'educational',
        // ... 其他配置
    },
    currentResult: null        // 当前生成结果
};
```

## 注意事项

1. **图片库必须存在**: `image_library/` 文件夹至少要有一张图片
2. **API密钥**: GLM用于文本生成，MiniMax用于图像和TTS
3. **FFmpeg**: 视频剪辑需要ffmpeg在PATH中
4. **GPU**: 建议使用GPU加速模型推理
