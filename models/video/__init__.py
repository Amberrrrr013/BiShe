"""
图生视频模块
支持:
1. Wav2Lip - 唇形同步视频生成
2. SadTalker - 高质量头部动�?
3. 在线API - Runway/Pika�?
"""
import os
import sys
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import WAV2LIP_MODEL_PATH, SADTALKER_MODEL_PATH, API_CONFIG, WAV2LIP_PY, SADTALKER_PY, OUTPUT_DIR


@dataclass
class VideoResult:
    """视频生成结果"""
    video_path: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    success: bool = True
    error_msg: str = ""


class VideoProvider(ABC):
    """视频生成提供者抽象基�?""
    
    @abstractmethod
    def generate(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None,
        **kwargs
    ) -> VideoResult:
        """
        生成视频
        
        Args:
            image_path: 输入图像路径
            audio_path: 输入音频路径
            output_path: 输出视频路径
            
        Returns:
            VideoResult
        """
        pass


class Wav2LipProvider(VideoProvider):
    """Wav2Lip 唇形同步视频生成"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(WAV2LIP_MODEL_PATH)
        self._model = None
        self._face_detection = None
        
        # Wav2Lip模型权重文件
        checkpoint_dir = Path(self.model_path) / "checkpoints"
        if checkpoint_dir.exists():
            # 查找 .pth 文件
            pth_files = list(checkpoint_dir.glob("*.pth")) + list(checkpoint_dir.glob("*.pt"))
            if pth_files:
                self.checkpoint_path = pth_files[0]
            else:
                self.checkpoint_path = checkpoint_dir / "wav2lip_gan.pth"
        else:
            self.checkpoint_path = Path(self.model_path) / "wav2lip_gan.pth"
    
    def _load_models(self):
        if self._model is None:
            try:
                sys.path.insert(0, str(self.model_path))
                
                import torch
                from glob import glob
                
                # 查找权重文件
                wav2lip_path = None
                for pattern in ["*.pth", "*.pt", "wav2lip*.pth"]:
                    files = glob(str(self.checkpoint_path / pattern))
                    if files:
                        wav2lip_path = files[0]
                        break
                
                if wav2lip_path and Path(wav2lip_path).exists():
                    # 动态导入wav2lip模型
                    from models import Wav2Lip
                    
                    self._model = Wav2Lip()
                    checkpoint = torch.load(wav2lip_path, map_location='cuda')
                    self._model.load_state_dict(checkpoint)
                    self._model = self._model.cuda()
                    self._model.eval()
                
                # 加载人脸检测模�?
                import cv2
                self._face_detection = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                
            except Exception as e:
                print(f"加载Wav2Lip模型失败: {e}")
                self._model = None
    
    def generate(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None,
        resize_factor: int = 1,
        crop: tuple = None,
        box: list = None,
        rotate: bool = False,
        nosmooth: bool = False,
        pad: tuple = None
    ) -> VideoResult:
        """
        使用Wav2Lip生成唇形同步视频
        
        Args:
            image_path: 人脸图像路径
            audio_path: 音频路径
            output_path: 输出视频路径
            resize_factor: 缩放因子
            crop: 裁剪区域 (x,y,w,h)
            box: 人脸边界�?[x1,y1,x2,y2]
            rotate: 是否旋转图像
            nosmooth: 是否平滑
            pad: 填充 (top,bottom,left,right)
        """
        if not Path(image_path).exists():
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"图像文件不存�? {image_path}"
            )
        
        if not Path(audio_path).exists():
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"音频文件不存�? {audio_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{image_path}{audio_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "video"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"wav2lip_{hash_str}.mp4")
        
        # 由于Wav2Lip需要完整的推理脚本，这里提供一个简化的调用接口
        # 实际使用时可能需要调用项目中的inference.py
        try:
            self._load_models()
            
            # 如果模型加载成功，使�?Python 执行推理
            if self._model is not None:
                # TODO: 实现 Python 版本�?Wav2Lip 推理
                pass
            
            # 使用 subprocess 执行 inference.py（无论是模型加载失败还是正常流程�?
            # 构建推理命令 - 使用虚拟环境�?Python
            cmd = [
                str(WAV2LIP_PY),
                str(Path(self.model_path) / "inference.py"),
                "--checkpoint", str(self.checkpoint_path),
                "--face", str(image_path),
                "--audio", str(audio_path),
                "--outfile", str(output_path)
            ]
            
            if resize_factor != 1:
                cmd.extend(["--resize_factor", str(resize_factor)])
            if crop:
                cmd.extend(["--crop", " ".join(map(str, crop))])
            if box:
                cmd.extend(["--box", " ".join(map(str, box))])
            if rotate:
                cmd.append("--rotate")
            if nosmooth:
                cmd.append("--nosmooth")
            if pad:
                cmd.extend(["--pad", " ".join(map(str, pad))])
            
            # 执行推理
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.model_path)
            )
            
            if result.returncode != 0:
                return VideoResult(
                    video_path="",
                    success=False,
                    error_msg=f"Wav2Lip推理失败: {result.stderr}"
                )
            
            if not Path(output_path).exists():
                return VideoResult(
                    video_path="",
                    success=False,
                    error_msg="Wav2Lip未生成输出文�?
                )
            
            # 获取视频信息
            duration, width, height = self._get_video_info(output_path)
            
            return VideoResult(
                video_path=output_path,
                duration=duration,
                width=width,
                height=height
            )
            
        except Exception as e:
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"Wav2Lip生成失败: {e}"
            )
    
    def _get_video_info(self, video_path: str) -> Tuple[float, int, int]:
        """获取视频信息"""
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        duration = frame_count / fps if fps > 0 else 0
        return duration, width, height


class SadTalkerProvider(VideoProvider):
    """SadTalker 高质量头部动�?""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(SADTALKER_MODEL_PATH)
        self._setup_paths()
    
    def _setup_paths(self):
        """设置SadTalker路径"""
        self.sadtalker_dir = Path(self.model_path)
        
        # 检查必要的子目�?
        self.checkpoints_dir = self.sadtalker_dir / "checkpoints"
        self.examples_dir = self.sadtalker_dir / "examples"
        
        # 查找推理脚本
        self.inference_script = self.sadtalker_dir / "inference.py"
        if not self.inference_script.exists():
            self.inference_script = self.sadtalker_dir / "推理.py"
    
    def generate(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None,
        expression_scale: float = 1.0,
        still_mode: bool = False,
        size: int = 512,
        batch_size: int = 2,  # 批处理大小，默认2提升速度
        video_type: str = "webp",
        fp16: bool = True  # 启用FP16加速，显著提升速度
    ) -> VideoResult:
        """
        使用SadTalker生成头部动画视频
        
        Args:
            image_path: 人脸图像路径
            audio_path: 音频路径
            output_path: 输出视频路径
            expression_scale: 表情强度 (0.5-1.5)
            still_mode: 是否使用静态模�?
            size: 输出视频尺寸
            batch_size: 批处理大�?
            video_type: 输出视频类型 (mp4/webp)
            fp16: 是否启用FP16混合精度加速（显著提升速度，降低质量不明显�?
        """
        if not Path(image_path).exists():
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"图像文件不存�? {image_path}"
            )
        
        if not Path(audio_path).exists():
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"音频文件不存�? {audio_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{image_path}{audio_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "video"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"sadtalker_{hash_str}.mp4")
        
        try:
            # 构建推理命令 - 使用虚拟环境�?Python
            cmd = [
                str(SADTALKER_PY), str(self.inference_script),
                "--driven_audio", str(audio_path),
                "--source_image", str(image_path),
                "--result_dir", str(Path(output_path).parent),
                "--expression_scale", str(expression_scale),
                "--size", str(size),
                "--batch_size", str(batch_size),
                # GFPGAN disabled
            ]
            
            # 添加FP16加速参数（显著提升速度�?
            if fp16:
                cmd.append("--fp16")
            
            if still_mode:
                cmd.append("--still")
            
            # 执行推理 - 使用线程实时获取输出以便显示进度
            import subprocess
            import threading
            import os
            
            # 设置CUDA优化环境变量
            env = os.environ.copy()
            env['CUDA_LAUNCH_BLOCKING'] = '1'  # 同步CUDA调用以便更好地错误诊�?
            if fp16:
                env['TORCH_CUDNN_V8_API_ENABLED'] = '1'  # 启用CUDNN v8 API
            
            # 进度映射：SadTalker的print语句 -> 进度百分�?
            progress_steps = [
                ("3DMM Extraction for source image", 10),
                ("3DMM Extraction for the reference video providing eye blinking", 25),
                ("3DMM Extraction for the reference video providing pose", 40),
                ("audio2ceoff", 50),
                ("coeff2video", 60),
                ("The generated video is named", 95),
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(self.sadtalker_dir),
                env=env  # 传入优化后的环境变量
            )
            
            # 使用线程读取输出，避免阻�?
            output_lines = []
            error_lines = []
            progress = [0]  # 使用列表以便在线程中修改
            
            def read_output(pipe, lines, is_stderr=False):
                for line in pipe:
                    line = line.rstrip('\n')
                    if is_stderr:
                        error_lines.append(line)
                        print(f"[SadTalker Error] {line}")
                    else:
                        lines.append(line)
                        print(f"[SadTalker] {line}")
                        # 解析进度
                        for keyword, prog in progress_steps:
                            if keyword in line:
                                old_progress = progress[0]
                                progress[0] = prog
                                if prog > old_progress:
                                    print(f"[SadTalker 进度] {prog}%")
            
            # 启动读取线程
            stdout_thread = threading.Thread(target=read_output, args=(process.stdout, output_lines, False))
            stderr_thread = threading.Thread(target=read_output, args=(process.stderr, error_lines, True))
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待进程结束，每10秒检查一次进�?
            import time
            last_progress = 0
            while process.poll() is None:
                time.sleep(10)
                if progress[0] == last_progress and progress[0] < 95:
                    print(f"[SadTalker 仍在运行...] 当前进度: {progress[0]}%, GPU应接�?00%")
                last_progress = progress[0]
            
            # 等待所有输出读取完�?
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            if process.returncode != 0:
                error_msg = "\n".join(error_lines) if error_lines else "Unknown error"
                return VideoResult(
                    video_path="",
                    success=False,
                    error_msg=f"SadTalker推理失败: {error_msg}"
                )
            
            # 查找生成的视频文�?
            output_dir_path = Path(output_path).parent
            video_files = list(output_dir_path.glob("*.mp4")) + list(output_dir_path.glob("*.webp"))
            
            if not video_files:
                return VideoResult(
                    video_path="",
                    success=False,
                    error_msg="SadTalker未生成输出文�?
                )
            
            # 使用最新的视频文件
            generated_video = max(video_files, key=lambda p: p.stat().st_mtime)
            
            # 如果需要移动到指定路径
            if str(generated_video) != output_path:
                import shutil
                shutil.move(str(generated_video), output_path)
            
            # 清理GPU内存
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
            except:
                pass
            
            duration, width, height = self._get_video_info(output_path)
            
            return VideoResult(
                video_path=output_path,
                duration=duration,
                width=width,
                height=height
            )
            
        except Exception as e:
            # 发生异常时也尝试清理GPU内存
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"SadTalker生成失败: {e}"
            )
    
    def _get_video_info(self, video_path: str) -> Tuple[float, int, int]:
        """获取视频信息"""
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        duration = frame_count / fps if fps > 0 else 0
        return duration, width, height


class OnlineVideoProvider(VideoProvider):
    """在线视频生成API (Runway/Pika�?"""
    
    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG.get("video_api", {})
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            provider = self.api_config.get("provider", "runway")
            
            if provider == "runway":
                try:
                    import stability_sdk
                    self._client = stability_sdk
                except ImportError:
                    raise ImportError("请安装stability-sdk")
            elif provider == "pika":
                # Pika API客户�?
                pass
        
        return self._client
    
    def generate(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None,
        prompt: str = None,
        duration: int = 4
    ) -> VideoResult:
        """
        使用在线API生成视频
        
        Args:
            image_path: 初始图像
            audio_path: 音频文件 (用于音视频同�?
            output_path: 输出视频路径
            prompt: 视频描述提示�?
            duration: 视频时长(�?
        """
        provider = self.api_config.get("provider", "runway")
        
        if output_path is None:
            hash_str = hashlib.md5(f"{image_path}{audio_path}".encode()).hexdigest()[:8]
            output_dir = Path(__file__).parent.parent / "output" / "video"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"online_{hash_str}.mp4")
        
        if provider == "runway":
            return self._generate_runway(image_path, audio_path, output_path, prompt, duration)
        elif provider == "pika":
            return self._generate_pika(image_path, audio_path, output_path, prompt, duration)
        else:
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"不支持的视频生成provider: {provider}"
            )
    
    def _generate_runway(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        prompt: str,
        duration: int
    ) -> VideoResult:
        """Runway ML视频生成"""
        api_key = self.api_config.get("api_key")
        
        if not api_key:
            return VideoResult(
                video_path="",
                success=False,
                error_msg="缺少Runway API密钥"
            )
        
        try:
            import requests
            
            # 1. 上传图像
            with open(image_path, "rb") as f:
                image_upload = requests.post(
                    "https://api.runwayml.com/v1/images",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"image": f}
                ).json()
            
            image_id = image_upload.get("id")
            
            # 2. 创建视频生成任务
            task_response = requests.post(
                "https://api.runwayml.com/v1/videos",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "image_id": image_id,
                    "prompt": prompt or "A person speaking",
                    "duration": duration
                }
            ).json()
            
            task_id = task_response.get("id")
            
            # 3. 轮询等待完成
            import time
            while True:
                status_response = requests.get(
                    f"https://api.runwayml.com/v1/videos/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                ).json()
                
                status = status_response.get("status")
                
                if status == "succeeded":
                    # 下载视频
                    video_url = status_response.get("output", {}).get("url")
                    if video_url:
                        video_response = requests.get(video_url)
                        with open(output_path, "wb") as f:
                            f.write(video_response.content)
                    
                    duration, width, height = self._get_video_info(output_path)
                    
                    return VideoResult(
                        video_path=output_path,
                        duration=duration,
                        width=width,
                        height=height
                    )
                elif status == "failed":
                    return VideoResult(
                        video_path="",
                        success=False,
                        error_msg="视频生成失败"
                    )
                
                time.sleep(5)
                
        except Exception as e:
            return VideoResult(
                video_path="",
                success=False,
                error_msg=f"Runway API调用失败: {e}"
            )
    
    def _generate_pika(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        prompt: str,
        duration: int
    ) -> VideoResult:
        """Pika视频生成"""
        # Pika API实现
        return VideoResult(
            video_path="",
            success=False,
            error_msg="Pika API尚未实现"
        )
    
    def _get_video_info(self, video_path: str) -> Tuple[float, int, int]:
        """获取视频信息"""
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        duration = frame_count / fps if fps > 0 else 0
        return duration, width, height


class VideoManager:
    """视频管理�?- 统一接口"""
    
    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or API_CONFIG
        self.providers = {
            "wav2lip": Wav2LipProvider(),
            "sadtalker": SadTalkerProvider(),
            "online": OnlineVideoProvider(self.api_config)
        }
    
    def generate_video(
        self,
        image_path: str,
        audio_path: str,
        method: str = "sadtalker",
        output_path: str = None,
        **kwargs
    ) -> VideoResult:
        """
        生成视频
        
        Args:
            image_path: 输入图像路径
            audio_path: 输入音频路径
            method: 视频生成方法 ("wav2lip", "sadtalker", "online")
            output_path: 输出视频路径
            **kwargs: 其他参数传递给具体provider
            
        Returns:
            VideoResult
        """
        if method not in self.providers:
            raise ValueError(f"未知的视频生成方�? {method}")
        
        provider = self.providers[method]
        return provider.generate(image_path, audio_path, output_path, **kwargs)
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        import cv2
        
        if not Path(video_path).exists():
            return {}
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": frame_count / fps if fps > 0 else 0
        }


