"""
图像处理模块
支持4种模式:
1. 用户即时拍摄照片
2. 用户上传的固定人像图片
3. 网上选好的公开人像图片
4. 调用API自动生成图像

支持GFPGAN超采样
"""
import hashlib
import shutil
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import GFPGAN_MODEL_PATH, API_CONFIG, OUTPUT_DIR
from config import PROJECT_ROOT


@dataclass
class ImageResult:
    """图像处理结果"""
    image_path: str
    width: int = 0
    height: int = 0
    success: bool = True
    error_msg: str = ""


class ImageProvider(ABC):
    """图像提供者抽象基类"""
    
    @abstractmethod
    def get_image(self, source: str, output_path: str) -> ImageResult:
        """
        获取图像
        
        Args:
            source: 图像来源 (路径/URL/提示词等)
            output_path: 输出路径
            
        Returns:
            ImageResult
        """
        pass


class CameraCaptureProvider(ImageProvider):
    """用户即时拍摄照片"""
    
    def __init__(self):
        self._camera = None
    
    def _init_camera(self):
        if self._camera is None:
            try:
                import cv2
                self._camera = cv2
            except ImportError:
                raise ImportError("请安装opencv-python: pip install opencv-python")
    
    def get_image(self, source: str = None, output_path: str = None) -> ImageResult:
        """
        拍摄照片
        
        Args:
            source: 可选，摄像头设备索引或None(使用默认)
            output_path: 输出路径
        """
        self._init_camera()
        
        if output_path is None:
            hash_str = hashlib.md5(str(source or "camera").encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "image"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"camera_{hash_str}.jpg")
        
        # 打开摄像头
        device_idx = int(source) if source else 0
        cap = self._camera.VideoCapture(device_idx)
        
        if not cap.isOpened():
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"无法打开摄像头 {device_idx}"
            )
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return ImageResult(
                image_path="",
                success=False,
                error_msg="无法从摄像头读取画面"
            )
        
        self._camera.imwrite(output_path, frame)
        
        h, w = frame.shape[:2]
        
        return ImageResult(
            image_path=output_path,
            width=w,
            height=h
        )


class LocalImageProvider(ImageProvider):
    """用户上传的固定人像图片"""
    
    def get_image(self, source: str, output_path: str = None) -> ImageResult:
        """
        复制用户提供的本地图片
        
        Args:
            source: 图片路径
            output_path: 输出路径
        """
        source_path = Path(source)
        
        if not source_path.exists():
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"图片文件不存在: {source}"
            )
        
        # 检查文件类型
        allowed_ext = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        if source_path.suffix.lower() not in allowed_ext:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"不支持的图片格式: {source_path.suffix}"
            )
        
        if output_path is None:
            output_dir = OUTPUT_DIR / "image"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"uploaded_{source_path.name}")
        
        # 复制文件
        shutil.copy2(source, output_path)
        
        # 获取图片尺寸
        import cv2
        img = cv2.imread(output_path)
        if img is None:
            return ImageResult(
                image_path="",
                success=False,
                error_msg="无法读取图片"
            )
        
        h, w = img.shape[:2]
        
        return ImageResult(
            image_path=output_path,
            width=w,
            height=h
        )


class URLImageProvider(ImageProvider):
    """网上选好的公开人像图片"""
    
    def get_image(self, source: str, output_path: str = None) -> ImageResult:
        """
        从URL下载图片
        
        Args:
            source: 图片URL
            output_path: 输出路径
        """
        import requests
        
        if output_path is None:
            hash_str = hashlib.md5(source.encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "image"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"url_{hash_str}.jpg")
        
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # 获取图片尺寸
            import cv2
            img = cv2.imread(output_path)
            if img is None:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg="下载的图片无法读取"
                )
            
            h, w = img.shape[:2]
            
            return ImageResult(
                image_path=output_path,
                width=w,
                height=h
            )
            
        except requests.exceptions.RequestException as e:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"下载图片失败: {e}"
            )


class APIGenerateProvider(ImageProvider):
    """调用API自动生成图像"""
    
    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG.get("image_api", {})
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            provider = self.api_config.get("provider", "openai")

            if provider == "openai":
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=self.api_config.get("api_key", ""))
                except ImportError:
                    raise ImportError("请安装openai: pip install openai")
            elif provider == "stability":
                try:
                    import stability_sdk
                    self._client = stability_sdk
                except ImportError:
                    raise ImportError("请安装stability-sdk")
            elif provider == "glm":
                # GLM uses OpenAI-compatible client
                try:
                    from openai import OpenAI
                    self._client = OpenAI(
                        api_key=self.api_config.get("api_key", ""),
                        base_url=self.api_config.get("base_url", "https://api.bigmodel.cn/api/paas/v4")
                    )
                except ImportError:
                    raise ImportError("请安装openai: pip install openai")

        return self._client
    
    def get_image(self, source: str, output_path: str = None, **kwargs) -> ImageResult:
        """
        根据提示词生成图像
        
        Args:
            source: 图像描述/提示词
            output_path: 输出路径
            **kwargs: 额外参数 (gender, age, expression, background, api_provider)
        """
        # 优先使用传入的api_provider，否则使用配置中的默认provider
        provider = kwargs.pop('api_provider', None) or self.api_config.get("provider", "minimax")
        
        if output_path is None:
            hash_str = hashlib.md5(source.encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "image"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"generated_{hash_str}.png")
        
        if provider == "openai":
            return self._generate_dalle(source, output_path, **kwargs)
        elif provider == "stability":
            return self._generate_stability(source, output_path, **kwargs)
        elif provider == "glm":
            return self._generate_glm(source, output_path, **kwargs)
        elif provider == "minimax":
            return self._generate_minimax(source, output_path, **kwargs)
        else:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"不支持的图像生成provider: {provider}"
            )
    
    def _generate_dalle(self, prompt: str, output_path: str, **kwargs) -> ImageResult:
        # 使用丰富的提示词模板构建半身人像
        gender = kwargs.get('gender', 'female')
        age = kwargs.get('age', 'young_adult')
        expression = kwargs.get('expression', 'happy')
        background = kwargs.get('background', 'classroom')
        full_prompt = self._build_portrait_prompt(prompt, gender, age, expression, background)
        
        client = self._get_client()
        
        try:
            response = client.images.generate(
                model=self.api_config.get("model", "dall-e-3"),
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # 下载图像
            import requests
            response = requests.get(image_url)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # 获取尺寸
            import cv2
            img = cv2.imread(output_path)
            if img is not None:
                h, w = img.shape[:2]
            else:
                w, h = 1024, 1024
            
            return ImageResult(
                image_path=output_path,
                width=w,
                height=h
            )
            
        except Exception as e:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"DALL-E生成失败: {e}"
            )
    
    def _generate_stability(self, prompt: str, output_path: str, **kwargs) -> ImageResult:
        # 使用丰富的提示词模板构建半身人像
        gender = kwargs.get('gender', 'female')
        age = kwargs.get('age', 'young_adult')
        expression = kwargs.get('expression', 'happy')
        background = kwargs.get('background', 'classroom')
        full_prompt = self._build_portrait_prompt(prompt, gender, age, expression, background)
        
        # Stability AI 生成逻辑
        return ImageResult(
            image_path="",
            success=False,
            error_msg="Stability AI 尚未实现"
        )

    def _build_portrait_prompt(self, topic: str, gender: str, age: str, expression: str, background: str) -> str:
        """
        构建人像提示词模板 - 证件照风格半身照
        
        Args:
            topic: 用户主题/场景描述
            gender: 性别 (female/male)
            age: 年龄段 (child/teenager/young_adult/middle_aged/elderly/senior)
            expression: 表情 (happy/sad/angry/passionate/calm/surprised)
            background: 背景 (classroom/nature/office/park/beach/city/library/starry)
            
        Returns:
            构建好的完整提示词
        """
        # 性别外貌描述 - 重点强化
        gender_appearance_map = {
            'female': {
                'base': 'female person',
                'face': 'soft facial features, clear bright eyes, neat eyebrows, gentle expression',
                'skin': 'healthy natural skin, good complexion',
                'hair': 'clean tidy hairstyle, natural dark hair',
                'attire': 'professional collared shirt or blouse'
            },
            'male': {
                'base': 'male person',
                'face': 'friendly facial features, clear bright eyes, neat eyebrows, confident expression',
                'skin': 'healthy natural skin, good complexion',
                'hair': 'clean short hairstyle, natural dark hair',
                'attire': 'professional collared dress shirt'
            }
        }
        
        # 年龄段强化描述
        age_detail_map = {
            'child': 'child about 10 years old, youthful innocent look, fresh smooth face, big clever eyes',
            'teenager': 'teenager about 16 years old, youthful energetic look, fresh clear skin, confident',
            'young_adult': 'young adult about 25 years old, fresh vibrant look, healthy energetic vibe',
            'middle_aged': 'middle-aged about 45 years old, mature dignified look, experienced trustworthy vibe',
            'elderly': 'elderly person about 60 years old, graceful aging look, wise gentle presence',
            'senior': 'senior person about 75 years old, distinguished aging look, peaceful wise presence'
        }
        
        # 表情强化描述
        expression_detail_map = {
            'happy': 'natural happy smile, warm friendly eyes, cheerful approachable mood',
            'sad': 'slight serious expression, calm thoughtful eyes, quiet professional mood',
            'angry': 'stern focused expression, determined serious eyes, authoritative presence',
            'passionate': 'enthusiastic expression, bright energetic eyes, speaking with passion',
            'calm': 'serene peaceful expression, gentle calm eyes, trustworthy composed mood',
            'surprised': 'slight alert expression, wide attentive eyes, curious interested look'
        }
        
        # 背景弱化 - 简单纯色
        background_simple_map = {
            'classroom': 'clean simple classroom, soft wall background, neat and professional',
            'nature': 'simple outdoor setting, soft green nature background, natural lighting',
            'office': 'simple office setting, clean wall background, professional environment',
            'park': 'simple park setting, soft green background, relaxed natural atmosphere',
            'beach': 'simple beach setting, soft blue sky background, sunny relaxed atmosphere',
            'city': 'simple city setting, modern clean background, professional urban feel',
            'library': 'simple library setting, warm wood tones background, scholarly atmosphere',
            'starry': 'simple dark blue background, subtle night sky, peaceful magical atmosphere'
        }
        
        # 获取描述
        gender_info = gender_appearance_map.get(gender, gender_appearance_map['female'])
        age_desc = age_detail_map.get(age, age_detail_map['young_adult'])
        expr_desc = expression_detail_map.get(expression, expression_detail_map['happy'])
        bg_desc = background_simple_map.get(background, background_simple_map['classroom'])
        
        # 构建半身人像提示词
        full_prompt = (
            f"Portrait photo of {gender_info['base']}. "
            f"Face: {gender_info['face']}. Skin: {gender_info['skin']}. "
            f"Hair: {gender_info['hair']}. Clothes: {gender_info['attire']}. "
            f"Age: {age_desc}. "
            f"Expression: {expr_desc}. "
            f"Setting: {bg_desc}. "
            f"Composition: person in center, head and upper body visible, "
            f"head takes up most of frame, professional photo style. "
            f"Clear focus on face, sharp image, high quality, "
            f"natural lighting on face, clean background, "
            f"realistic photo, not drawing or cartoon. "
            f"Topic: {topic}"
        )
        
        return full_prompt
        
        return full_prompt

    def _generate_glm(self, prompt: str, output_path: str, **kwargs) -> ImageResult:
        """GLM CogView-3-Flash 图片生成"""
        import requests
        import base64

        try:
            # 提取风格参数
            gender = kwargs.get('gender', 'female')
            age = kwargs.get('age', 'young_adult')
            expression = kwargs.get('expression', 'happy')
            background = kwargs.get('background', 'classroom')
            
            # 构建人像提示词模板
            full_prompt = self._build_portrait_prompt(prompt, gender, age, expression, background)
            
            api_key = self.api_config.get("api_key", "")
            model = self.api_config.get("model", "cogview-3-flash")
            base_url = self.api_config.get("base_url", "https://open.bigmodel.cn/api/paas/v4")

            url = f"{base_url}/images/generations"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model,
                "prompt": full_prompt,
                "quality": "standard",  # standard: 5-10秒生成; hd: 20秒更精细
                "size": "1280x1280",  # GLM推荐尺寸
                "watermark_enabled": False  # 关闭水印
            }

            print(f"[GLM Image] Generating image with model: {model}")
            print(f"[GLM Image] Full Prompt: {full_prompt[:200]}...")

            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code != 200:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg=f"GLM API错误: {response.status_code} - {response.text[:500]}"
                )

            result = response.json()
            print(f"[GLM Image] Response: {result}")

            # GLM返回格式可能是 base64 或 url
            image_data = result.get("data", [{}])[0].get("b64_json") or result.get("data", [{}])[0].get("url")

            if not image_data:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg="GLM返回的图像数据为空"
                )

            # 如果是base64，直接解码
            if isinstance(image_data, str) and len(image_data) > 1000:
                # 可能是base64
                try:
                    image_bytes = base64.b64decode(image_data)
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                except Exception:
                    # 如果不是base64，可能是URL，下载它
                    img_response = requests.get(image_data, timeout=60)
                    img_response.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
            else:
                # 是URL，下载图像
                img_response = requests.get(image_data, timeout=60)
                img_response.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(img_response.content)

            # 获取尺寸
            import cv2
            img = cv2.imread(output_path)
            if img is not None:
                h, w = img.shape[:2]
            else:
                w, h = 1024, 1024

            print(f"[GLM Image] Success! Saved to: {output_path}")

            return ImageResult(
                image_path=output_path,
                width=w,
                height=h
            )

        except Exception as e:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"GLM图片生成失败: {e}"
            )

    def _generate_minimax(self, prompt: str, output_path: str, **kwargs) -> ImageResult:
        """MiniMax image-01 图片生成"""
        import requests
        
        try:
            # 提取风格参数并构建完整提示词
            gender = kwargs.get('gender', 'female')
            age = kwargs.get('age', 'young_adult')
            expression = kwargs.get('expression', 'happy')
            background = kwargs.get('background', 'classroom')
            
            # 构建人像提示词模板
            full_prompt = self._build_portrait_prompt(prompt, gender, age, expression, background)
            
            api_key = self.api_config.get("api_key", "")
            model = self.api_config.get("model", "image-01")
            base_url = self.api_config.get("base_url", "https://api.minimaxi.com")
            aspect_ratio = self.api_config.get("aspect_ratio", "1:1")
            style_type = self.api_config.get("style_type", "")
            aigc_watermark = self.api_config.get("aigc_watermark", False)
            
            url = f"{base_url}/v1/image_generation"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "aspect_ratio": aspect_ratio,
                "response_format": "url",
                "aigc_watermark": aigc_watermark
            }
            
            # 如果有style_type且模型支持，添加style设置
            if style_type and model == "image-01-live":
                payload["style"] = {
                    "style_type": style_type,
                    "style_weight": 0.8
                }
            
            print(f"[MiniMax Image] Generating image with model: {model}")
            print(f"[MiniMax Image] Prompt: {full_prompt[:100]}...")
            print(f"[MiniMax Image] Aspect ratio: {aspect_ratio}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg=f"MiniMax API错误: {response.status_code} - {response.text[:500]}"
                )
            
            result = response.json()
            print(f"[MiniMax Image] Response: {result}")
            
            # 检查API返回状态
            base_resp = result.get("base_resp", {})
            if base_resp.get("status_code", 0) != 0:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg=f"MiniMax API错误: {base_resp.get('status_msg', 'Unknown error')}"
                )
            
            # 获取图片URL
            image_urls = result.get("data", {}).get("image_urls", [])
            if not image_urls:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg="MiniMax返回的图像数据为空"
                )
            
            image_url = image_urls[0]
            
            # 下载图像
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_response.content)
            
            # 获取尺寸
            import cv2
            img = cv2.imread(output_path)
            if img is not None:
                h, w = img.shape[:2]
            else:
                # 默认尺寸根据aspect_ratio
                if aspect_ratio == "16:9":
                    w, h = 1280, 720
                elif aspect_ratio == "4:3":
                    w, h = 1152, 864
                elif aspect_ratio == "3:2":
                    w, h = 1248, 832
                else:
                    w, h = 1024, 1024
            
            print(f"[MiniMax Image] Success! Saved to: {output_path}")
            
            return ImageResult(
                image_path=output_path,
                width=w,
                height=h
            )
            
        except Exception as e:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"MiniMax图片生成失败: {e}"
            )


class GFPGANEnhancer:
    """GFPGAN图像超采样增强"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(GFPGAN_MODEL_PATH)
        self._model = None
        # 导入配置中的 Python 解释器路径
        from config import GFPGAN_PY
        self.gfpgan_py = str(GFPGAN_PY)
    
    def _load_model(self):
        if self._model is None:
            try:
                sys.path.insert(0, self.model_path)
                from gfpgan import GFPGANer
                
                model_path = Path(self.model_path) / "GFPGANv1.4.pth"
                
                self._model = GFPGANer(
                    model_path=str(model_path) if model_path.exists() else "GFPGANv1.4.pth",
                    upscale=2,
                    arch='clean',
                    channel_multiplier=2
                )
            except Exception as e:
                raise RuntimeError(f"加载GFPGAN模型失败: {e}")
    
    def enhance(self, input_path: str, output_path: str = None) -> ImageResult:
        """
        对图像进行超采样增强 - 使用子进程调用GFPGAN虚拟环境
        
        Args:
            input_path: 输入图像路径
            output_path: 输出路径
            
        Returns:
            ImageResult
        """
        if not Path(input_path).exists():
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"输入图像不存在: {input_path}"
            )
        
        input_p = Path(input_path)
        if output_path is None:
            output_dir = input_p.parent
            output_path = str(output_dir / f"{input_p.stem}_enhanced{input_p.suffix}")
        
        # 创建临时脚本
        import tempfile
        import subprocess
        
        script_content = f'''
import sys
sys.path.insert(0, r"{self.model_path}")
from gfpgan import GFPGANer
import cv2

print("GFPGAN进度: 正在加载模型...")
model = GFPGANer(
    model_path=r"{Path(self.model_path) / 'GFPGANv1.4.pth'}",
    upscale=2,
    arch='clean',
    channel_multiplier=2
)
print("GFPGAN进度: 模型加载完成，正在处理图像...")

img = cv2.imread(r"{input_path}")
print("GFPGAN进度: 正在进行图像增强...")
_, _, restored = model.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
print("GFPGAN进度: 正在保存增强后的图像...")
cv2.imwrite(r"{output_path}", restored)
print("GFPGAN完成: 图像增强成功")
'''
        
        # 写入临时脚本
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # 使用 GFPGAN 虚拟环境的 Python 执行脚本
            result = subprocess.run(
                [self.gfpgan_py, script_path],
                capture_output=True,
                text=True,
                cwd=self.model_path,
                timeout=600
            )
            
            # 打印 GFPGAN 的进度输出
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  [GFPGAN] {line}")
            
            if result.returncode != 0:
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg=f"GFPGAN推理失败: {result.stderr}"
                )
            
            if not Path(output_path).exists():
                return ImageResult(
                    image_path="",
                    success=False,
                    error_msg="GFPGAN未生成输出文件"
                )
            
            # 获取图像尺寸
            import cv2
            img = cv2.imread(output_path)
            h, w = img.shape[:2] if img is not None else (0, 0)
            
            return ImageResult(
                image_path=output_path,
                width=w,
                height=h
            )
            
        except subprocess.TimeoutExpired:
            return ImageResult(
                image_path="",
                success=False,
                error_msg="GFPGAN处理超时"
            )
        except Exception as e:
            return ImageResult(
                image_path="",
                success=False,
                error_msg=f"GFPGAN增强失败: {e}"
            )
        finally:
            # 清理临时脚本
            if Path(script_path).exists():
                Path(script_path).unlink()


class ImageManager:
    """图像管理器 - 统一接口"""
    
    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG
        self.providers = {
            "camera": CameraCaptureProvider(),
            "upload": LocalImageProvider(),
            "url": URLImageProvider(),
            "api": APIGenerateProvider(self.api_config)
        }
        self.enhancer = GFPGANEnhancer()
        self._library = None  # 延迟加载图片库
    
    def _get_library(self):
        """获取图片库实例（延迟加载）"""
        if self._library is None:
            from skills import ImageLibrary
            self._library = ImageLibrary()
        return self._library
    
    def get_image(
        self,
        mode: str,
        source: str,
        output_path: str = None,
        enhance: bool = False,
        **kwargs
    ) -> ImageResult:
        """
        获取图像
        
        Args:
            mode: 模式 ("camera", "upload", "url", "api", "library", "random")
            source: 来源 (路径/URL/提示词)
            output_path: 输出路径
            enhance: 是否使用GFPGAN增强
            **kwargs: 额外参数 (用于API模式: gender, age, expression, background)
            
        Returns:
            ImageResult
        """
        # 处理 library/random 模式（从图片库随机选择）
        if mode in ("library", "random"):
            return self._get_random_from_library(output_path)
        
        if mode not in self.providers:
            raise ValueError(f"未知的图像获取模式: {mode}")
        
        provider = self.providers[mode]
        result = provider.get_image(source, output_path, **kwargs)
        
        if not result.success:
            return result
        
        # 如果需要GFPGAN增强
        if enhance:
            enhanced_result = self.enhancer.enhance(result.image_path)
            if enhanced_result.success:
                return enhanced_result
            # 增强失败时返回原图
            print(f"GFPGAN增强失败: {enhanced_result.error_msg}, 使用原图")
        
        return result
    
    def _get_random_from_library(self, output_path: str = None) -> ImageResult:
        """从图片库随机获取图片"""
        library = self._get_library()
        random_image_path = library.get_random_image()
        
        if not random_image_path:
            return ImageResult(
                image_path="",
                success=False,
                error_msg="图片库为空，请先添加图片到 image_library 文件夹"
            )
        
        # 使用 LocalImageProvider 复制图片
        provider = self.providers["upload"]
        return provider.get_image(random_image_path, output_path)
    
    def save_image(self, image_data: bytes, filename: str) -> str:
        """保存图像数据"""
        output_dir = OUTPUT_DIR / "image"
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, "wb") as f:
            f.write(image_data)
        return str(filepath)
