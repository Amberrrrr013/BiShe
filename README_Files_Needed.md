# 配置文件参考

本项目需要配置两个文件才能正常运行。以下是这两个文件的完整内容，用户只需将对应的 API 密钥替换为自己申请的密钥即可。

---

## 一、config.py

```python
"""
配置模块 - 管理所有配置路径和参数
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# 自动加载 .env 文件
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# 模型路径配置 - 从环境变量读取，默认为项目父目录
# 设置 MODEL_ROOT 环境变量指向模型所在目录，例如 D:\_BiShe
PARENT_DIR = Path(os.getenv("MODEL_ROOT", str(PROJECT_ROOT.parent)))

# TTS模型路径
PIPER_MODEL_PATH = PARENT_DIR / "piper-tts" / "en_US-amy-medium.onnx"
XTTS_MODEL_PATH = PARENT_DIR / "xtts-v2"

# Whisper模型路径 (用于WER检测)
WHISPER_MODEL_PATH = PARENT_DIR / "faster-whisper"

# 视频生成模型路径
WAV2LIP_MODEL_PATH = PARENT_DIR / "wav2lip"
SADTALKER_MODEL_PATH = PARENT_DIR / "sadtalker"

# 图像处理模型路径
GFPGAN_MODEL_PATH = PARENT_DIR / "gfpgan"

# Kokoro TTS 模型路径
KOKORO_MODEL_PATH = PARENT_DIR / "kokoro-tts"

# 各模型虚拟环境的 Python 解释器路径
WAV2LIP_PY = WAV2LIP_MODEL_PATH / "env" / "Scripts" / "python.exe"
SADTALKER_PY = SADTALKER_MODEL_PATH / "env" / "Scripts" / "python.exe"
GFPGAN_PY = GFPGAN_MODEL_PATH / "env" / "Scripts" / "python.exe"
FASTER_WHISPER_PY = WHISPER_MODEL_PATH / "env" / "Scripts" / "python.exe"
PIPER_TTS_PY = PIPER_MODEL_PATH.parent / "env" / "Scripts" / "python.exe"
XTTS_PY = XTTS_MODEL_PATH / "env" / "Scripts" / "python.exe"
KOKORO_PY = KOKORO_MODEL_PATH / "env" / "Scripts" / "python.exe"

# 创建必要的输出目录
for subdir in ["text", "audio", "image", "video", "final"]:
    (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)

# WER阈值配置
WER_THRESHOLD = 0.15  # 15%错误率以内可接受
MAX_TTS_RETRIES = 5

# API配置 - 从环境变量读取，安全不泄露
def _get_env(key, default="", desc=""):
    """安全获取环境变量"""
    value = os.environ.get(key, default)
    if not value and default == "":
        print(f"[警告] 环境变量 {key} 未设置！{desc}")
    return value

# MiniMax API Key - 请设置环境变量 MINIMAX_API_KEY
MINIMAX_API_KEY = _get_env(
    "MINIMAX_API_KEY",
    desc="MiniMax API密钥，用于文本生成、TTS和图片生成"
)

# GLM API Key - 用于Agent模式文本生成
GLM_API_KEY = _get_env(
    "GLM_API_KEY",
    desc="GLM API密钥，用于Agent模式文本生成"
)

API_CONFIG = {
    "text_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "MiniMax-Text-01",
        "base_url": "https://api.minimaxi.com/v1"
    },
    "agent_api": {
        "provider": "glm",
        "api_key": GLM_API_KEY,
        "model": "GLM-4.6V-FlashX",
        "base_url": "https://open.bigmodel.cn/api/paas/v4"
    },
    "tts_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "speech-2.8-hd",
        "voice_id": "English_Graceful_Lady",
        "voice_options": [
            {"id": "English_Graceful_Lady", "name": "优雅女士 (English Graceful Lady)"},
            {"id": "Sweet_Girl", "name": "甜美女孩 (Sweet Girl)"},
            {"id": "English_Trustworthy_Man", "name": "可靠男士 (English Trustworthy Man)"}
        ],
        "base_url": "https://api.minimaxi.com",
        "voice": "en-US-JennyNeural"
    },
    "image_api": {
        "provider": "minimax",
        "api_key": MINIMAX_API_KEY,
        "model": "image-01",
        "base_url": "https://api.minimaxi.com",
        "aspect_ratio": "1:1",
        "style_type": "",
        "aigc_watermark": False
    },
    "video_api": {
        "provider": "local",
        "api_key": ""
    }
}
```

---

## 二、api_config.py

```python
"""
API配置管理模块 - 存储多个API选项供用户选择
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
API_CONFIG_FILE = PROJECT_ROOT / "api_keys.json"


class APIEntry:
    """单个API条目"""
    def __init__(self, name: str, provider: str, api_key: str = "", base_url: str = "", **kwargs):
        self.name = name  # 显示名称
        self.provider = provider  # 提供商
        self.api_key = api_key  # API密钥
        self.base_url = base_url  # 自定义URL（可选）
        self.extra = kwargs  # 其他配置
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        result.update(self.extra)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIEntry':
        return cls(**data)


class APICategory:
    """API分类（文本/图像/语音/视频）"""
    def __init__(self, category: str, apis: List[APIEntry] = None):
        self.category = category
        self.apis: List[APIEntry] = apis or []
    
    def add_api(self, api: APIEntry):
        self.apis.append(api)
    
    def remove_api(self, name: str):
        self.apis = [a for a in self.apis if a.name != name]
    
    def get_api(self, name: str) -> Optional[APIEntry]:
        for api in self.apis:
            if api.name == name:
                return api
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "apis": [a.to_dict() for a in self.apis]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APICategory':
        apis = [APIEntry.from_dict(a) for a in data.get("apis", [])]
        return cls(data["category"], apis)


class APIManager:
    """API管理器 - 存储和加载API配置"""
    
    # 默认配置
    DEFAULT_CATEGORIES = {
        "text": APICategory("text", [
            APIEntry("MiniMax Claude", "minimax", 
                    api_key="你的MiniMax API密钥",
                    base_url="https://api.minimaxi.com/anthropic/v1",
                    model="MiniMax-Text-01",
                    group_id="你的GroupID"),
            APIEntry("OpenAI GPT-4o-mini", "openai", os.getenv("OPENAI_API_KEY", ""), model="gpt-4o-mini"),
            APIEntry("OpenAI GPT-4o", "openai", os.getenv("OPENAI_API_KEY", ""), model="gpt-4o"),
        ]),
        "image": APICategory("image", [
            APIEntry("OpenAI DALL-E-3", "openai", os.getenv("OPENAI_API_KEY", ""), model="dall-e-3"),
            APIEntry("MiniMax Image", "minimax",
                    api_key="你的MiniMax API密钥",
                    base_url="https://api.minimaxi.com",
                    model="image-01"),
            APIEntry("Stability AI", "stability", os.getenv("STABILITY_API_KEY", ""), model="stable-diffusion-xl-1024-v1-0"),
        ]),
        "tts": APICategory("tts", [
            APIEntry("Edge TTS", "edge", "", voice="en-US-JennyNeural"),
            APIEntry("MiniMax TTS", "minimax",
                    api_key="你的MiniMax API密钥",
                    base_url="https://api.minimaxi.com",
                    model="speech-02"),
        ]),
        "video": APICategory("video", [
            APIEntry("Wav2Lip (本地)", "local", model="wav2lip"),
            APIEntry("SadTalker (本地)", "local", model="sadtalker"),
        ])
    }
    
    def __init__(self):
        self.categories: Dict[str, APICategory] = {}
        self.load()
    
    def load(self):
        """从文件加载配置"""
        if API_CONFIG_FILE.exists():
            try:
                with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cat_data in data.get("categories", []):
                        cat = APICategory.from_dict(cat_data)
                        self.categories[cat.category] = cat
                
                # 确保所有默认分类都存在
                for name, default_cat in self.DEFAULT_CATEGORIES.items():
                    if name not in self.categories:
                        self.categories[name] = default_cat
            except Exception as e:
                print(f"加载API配置失败: {e}")
                self._init_defaults()
        else:
            self._init_defaults()
    
    def _init_defaults(self):
        """初始化默认配置"""
        self.categories = dict(self.DEFAULT_CATEGORIES)
    
    def save(self):
        """保存配置到文件"""
        data = {
            "categories": [cat.to_dict() for cat in self.categories.values()]
        }
        try:
            with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存API配置失败: {e}")
    
    def get_category(self, name: str) -> Optional[APICategory]:
        return self.categories.get(name)
    
    def get_all_categories(self) -> Dict[str, APICategory]:
        return self.categories
    
    def add_api(self, category: str, api: APIEntry):
        if category not in self.categories:
            self.categories[category] = APICategory(category)
        self.categories[category].add_api(api)
        self.save()
    
    def remove_api(self, category: str, name: str):
        if category in self.categories:
            self.categories[category].remove_api(name)
            self.save()
    
    def get_api_list(self, category: str) -> List[Dict[str, Any]]:
        """获取分类下的所有API选项（用于前端显示）"""
        if category not in self.categories:
            return []
        return [api.to_dict() for api in self.categories[category].apis]


# 全局API管理器实例
api_manager = APIManager()
```

---

## 三、.env 文件配置（可选）

`config.py` 支持从 `.env` 文件自动读取环境变量。在项目根目录创建 `.env` 文件：

```env
# MiniMax API 密钥
MINIMAX_API_KEY=你的MiniMax密钥

# GLM API 密钥（用于Agent模式）
GLM_API_KEY=你的GLM密钥
```

---

## 四、获取 API 密钥

| 服务 | 地址 |
|------|------|
| MiniMax | https://www.minimaxi.com |
| GLM | https://bigmodel.cn |
| OpenAI | https://platform.openai.com |
| Stability AI | https://platform.stability.ai |

---

## 五、优化建议

1. **安全考虑**：建议将敏感信息放在 `.env` 文件中，而不是直接写在代码里。本项目的 `.env` 文件已在 `.gitignore` 中排除，不会被提交到 GitHub。

2. **api_keys.json**：如果希望前端 API 管理界面持久化保存用户的自定义配置，可以创建 `api_keys.json` 文件（系统会优先读取该文件，而不是代码中的默认值）。

3. **环境变量**：可以使用 `os.getenv("变量名", "默认值")` 的方式从环境变量读取 API 密钥，这样在 CI/CD 或 Docker 部署时更加灵活。
