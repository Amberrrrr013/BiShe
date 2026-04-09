"""
视频剪辑模块
使用ffmpeg进行视频处理:
- 添加字幕
- 音视频合成
- 视频裁剪/缩放
"""
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR


@dataclass
class SubtitleInfo:
    """字幕信息"""
    start_time: float
    end_time: float
    text: str


@dataclass
class VideoEditResult:
    """视频编辑结果"""
    output_path: str
    success: bool
    error_msg: str = ""


class FFmpegWrapper:
    """FFmpeg封装器"""
    
    @staticmethod
    def run_command(cmd: List[str], capture_output: bool = True, cwd: str = None) -> Tuple[bool, str, str]:
        """
        执行ffmpeg命令
        
        Args:
            cmd: 命令列表
            capture_output: 是否捕获输出
            cwd: 工作目录
        
        Returns:
            Tuple[bool, str, str]: (成功标志, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
                cwd=cwd
            )
            
            success = result.returncode == 0
            return success, result.stdout or "", result.stderr or ""
            
        except FileNotFoundError:
            return False, "", "ffmpeg未安装或不在PATH中"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if not success:
            return {}
        
        try:
            info = json.loads(stdout)
            
            # 提取关键信息
            video_stream = None
            audio_stream = None
            
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                elif stream.get("codec_type") == "audio":
                    audio_stream = stream
            
            duration = float(info.get("format", {}).get("duration", 0))
            
            if video_stream:
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                fps = eval(video_stream.get("r_frame_rate", "0/1"))
            else:
                width, height, fps = 0, 0, 0
            
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": audio_stream is not None
            }
        except:
            return {}


class SubtitleGenerator:
    """字幕生成器"""
    
    def __init__(self):
        self.words_per_line = 8  # 每行显示的单词数
    
    def generate_from_text(
        self,
        text: str,
        word_timings: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        从文本和词级时间戳生成字幕文件
        
        Args:
            text: 原始文本
            word_timings: 词级时间信息列表 [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
            output_path: 输出srt文件路径
            
        Returns:
            str: srt文件路径
        """
        if not word_timings:
            return self._generate_simple_subtitles(text, output_path)
        
        # 按行分组
        lines = []
        current_line_words = []
        current_line_start = None
        current_line_end = None
        
        for i, word_info in enumerate(word_timings):
            word = word_info.get("word", "")
            start = word_info.get("start", 0)
            end = word_info.get("end", start + 0.5)
            
            current_line_words.append(word)
            if current_line_start is None:
                current_line_start = start
            current_line_end = end
            
            # 当达到每行单词数或这是最后一个词时，换行
            if len(current_line_words) >= self.words_per_line or i == len(word_timings) - 1:
                if current_line_words:
                    lines.append({
                        "text": " ".join(current_line_words),
                        "start": current_line_start,
                        "end": current_line_end
                    })
                    current_line_words = []
                    current_line_start = None
        
        # 写入SRT文件
        with open(output_path, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines, 1):
                start_time = self._format_srt_time(line["start"])
                end_time = self._format_srt_time(line["end"])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{line['text']}\n\n")
        
        return output_path
    
    def generate_from_segments(
        self,
        segments: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        从分段信息生成字幕
        
        Args:
            segments: 分段信息列表 [{"start": 0.0, "end": 5.0, "text": "Hello world"}, ...]
            output_path: 输出srt文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start_time = self._format_srt_time(segment["start"])
                end_time = self._format_srt_time(segment["end"])
                text = segment.get("text", "").strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        return output_path
    
    def _generate_simple_subtitles(
        self,
        text: str,
        output_path: str,
        duration: float = 10.0
    ) -> str:
        """生成简单字幕（平均分配时间）"""
        words = text.split()
        word_count = len(words)
        word_duration = duration / word_count if word_count > 0 else 1.0
        
        lines = []
        current_line_words = []
        current_time = 0.0
        
        for word in words:
            current_line_words.append(word)
            if len(current_line_words) >= self.words_per_line:
                line_text = " ".join(current_line_words)
                lines.append({
                    "text": line_text,
                    "start": current_time,
                    "end": current_time + word_duration * len(current_line_words)
                })
                current_time = lines[-1]["end"]
                current_line_words = []
        
        # 处理剩余的词
        if current_line_words:
            lines.append({
                "text": " ".join(current_line_words),
                "start": current_time,
                "end": current_time + word_duration * len(current_line_words) + 1.0
            })
        
        return self._write_srt(lines, output_path)
    
    def _write_srt(self, lines: List[Dict[str, Any]], output_path: str) -> str:
        """写入SRT文件"""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines, 1):
                start_time = self._format_srt_time(line["start"])
                end_time = self._format_srt_time(line["end"])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{line['text']}\n\n")
        
        return output_path
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """格式化SRT时间 (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """格式化ASS时间 (00:00:00.00)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _build_drawtext_filter(self, segments: List[Dict[str, Any]], width: int, height: int) -> str:
        """
        构建drawtext滤镜参数（用于备选方案）
        
        Args:
            segments: 分段信息列表
            width: 视频宽度
            height: 视频高度
            
        Returns:
            str: drawtext滤镜参数
        """
        filters = []
        y_position = height // 2  # 居中
        
        for i, seg in enumerate(segments):
            text = seg.get("text", "").replace("'", "\\'").replace(":", "\\:").replace("\n", " ")
            start = seg.get("start", 0)
            end = seg.get("end", 5)
            
            # 构建enable条件
            enable = f"between(t,{start},{end})"
            
            # 构建drawtext参数
            filter_str = (
                f"drawtext=text='{text}':"
                f"fontsize=36:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y={y_position}:"
                f"enable='{enable}'"
            )
            filters.append(filter_str)
        
        return ",".join(filters)
    
    def generate_srt_subtitle(
        self,
        segments: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        生成SRT字幕文件
        
        Args:
            segments: 分段信息列表 [{"start": 0.0, "end": 5.0, "text": "Hello world"}, ...]
            output_path: 输出srt文件路径
            
        Returns:
            str: srt文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start_time = self._format_srt_time(seg.get("start", 0))
                end_time = self._format_srt_time(seg.get("end", 5))
                text_content = seg.get("text", "").replace("\n", " ")
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text_content}\n\n")
        
        return output_path
    
    def generate_ass_subtitle(
        self,
        text: str,
        segments: List[Dict[str, Any]],
        output_path: str,
        mode: str = "fulltext",
        highlight_color: str = "&H00FF00&",
        video_width: int = 720,
        video_height: int = 960
    ) -> str:
        """
        生成带高亮效果的ASS字幕文件
        
        Args:
            text: 原始文本
            segments: 分段信息列表 [{"start": 0.0, "end": 5.0, "text": "Hello world"}, ...]
            output_path: 输出ass文件路径
            mode: "fulltext" - 显示完整文本，高亮当前句子
            highlight_color: 高亮颜色 (&HBBGGRR&格式)
            video_width: 视频宽度
            video_height: 视频高度
            
        Returns:
            str: ass文件路径
        """
        ass_header = f"""[Script Info]
Title: Highlighted Subtitle
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF&,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,5,10,10,30,1
Style: Highlight,Arial,36,&H00FF00FF&,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,5,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            
            # 计算总时间
            total_duration = max([seg["end"] for seg in segments]) if segments else 0
            
            if mode == "fulltext" and segments:
                # 获取完整文本的句子列表
                sentences = [seg["text"] for seg in segments]
                full_text = "\n".join(sentences)
                
                # 计算每行的高度（基于字体大小36，假设行高1.5倍）
                line_height = 54
                # 计算需要的垂直偏移，让当前高亮行在中间偏上
                base_y = 200
                
                # 为每个时间段创建字幕条目
                for i, seg in enumerate(segments):
                    start = seg["start"]
                    end = seg["end"]
                    
                    # 构建带高亮的ASS文本
                    # 当前句子之前的文本（灰色）
                    before_text = "\n".join(sentences[:i])
                    # 当前句子（高亮）
                    current_text = sentences[i]
                    # 当前句子之后的文本（灰色）
                    after_text = "\n".join(sentences[i+1:])
                    
                    # 构建ASS格式的文本
                    # {\pos(x,y)} 设置位置
                    # \fs36 设置字体大小
                    # \c&HRRGGBB& 设置颜色
                    # \b1 加粗
                    
                    ass_lines = []
                    
                    if before_text:
                        ass_lines.append(f"{{\\pos(40,{base_y})}}\\fs32\\c&H808080&{before_text}")
                    
                    # 高亮行：白色，加粗
                    # 计算高亮行的Y位置
                    highlight_y = base_y + i * line_height
                    ass_lines.append(f"{{\\pos(40,{highlight_y})}}\\fs36\\c&H00FF00&\\b1{current_text}")
                    
                    if after_text:
                        after_y = base_y + (i + 1) * line_height
                        ass_lines.append(f"{{\\pos(40,{after_y})}}\\fs32\\c&H808080&{after_text}")
                    
                    text_content = "\\N".join(ass_lines)
                    
                    start_time = self._format_ass_time(start)
                    end_time = self._format_ass_time(end + 0.1)  # 稍微延长一点避免闪烁
                    
                    f.write(f"Dialogue: 0,{start_time},{end_time},Highlight,,0,0,0,,{text_content}\n")
        
        return output_path


class VideoEditor:
    """视频编辑器"""
    
    def __init__(self):
        self.subtitle_generator = SubtitleGenerator()
    
    def add_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str = None,
        font: str = "Arial",
        font_size: int = 24,
        font_color: str = "white",
        background_color: str = "black@0.5",
        position: str = "bottom"  # bottom, top, center
    ) -> VideoEditResult:
        """
        为视频添加字幕
        
        Args:
            video_path: 输入视频路径
            subtitle_path: SRT字幕文件路径
            output_path: 输出视频路径
            font: 字体名称
            font_size: 字体大小
            font_color: 字体颜色
            background_color: 背景颜色 (@表示透明度)
            position: 字幕位置 (bottom, top, center)
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if not Path(subtitle_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"字幕文件不存在: {subtitle_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{video_path}{subtitle_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"subtitled_{hash_str}.mp4")
        
        # 设置字幕位置
        if position == "bottom":
            margin = "margin_bottom=40"
        elif position == "top":
            margin = "margin_top=40"
        else:
            margin = "margin_top=40:margin_bottom=40"
        
        # ffmpeg subtitles 滤镜在 Windows 上对绝对路径有 bug
        # 解决方案：切换到字幕文件所在目录，使用相对路径
        subtitle_file = Path(subtitle_path)
        video_file = Path(video_path)
        output_file_path = Path(output_path)
        
        # Windows 上使用反斜杠
        work_dir = None
        input_video = video_path
        input_subtitle = subtitle_path
        output_file = str(output_path)
        
        if ":" in str(subtitle_path) or str(subtitle_path).startswith("/"):
            # 检查视频和字幕是否在同一父目录
            same_parent = video_file.parent == subtitle_file.parent
            
            if same_parent:
                # 如果在同一目录，使用相对路径和 cwd
                work_dir = str(subtitle_file.parent)
                input_subtitle = subtitle_file.name
                input_video = video_file.name
                output_file = output_file_path.name
            else:
                # 如果不在同一目录，使用 cwd + 相对路径
                # 计算视频相对于字幕目录的相对路径
                try:
                    rel_video = video_file.relative_to(subtitle_file.parent)
                    input_video = str(rel_video).replace("/", "\\")
                except ValueError:
                    # 跨驱动器，假设视频在 ..\\video\\ 目录
                    input_video = "..\\video\\" + video_file.name
                
                work_dir = str(subtitle_file.parent)
                input_subtitle = subtitle_file.name
                
                # 计算输出文件相对于字幕目录的路径
                # 输出文件可能在 final 目录，需要计算正确的相对路径
                try:
                    rel_output = output_file_path.relative_to(subtitle_file.parent)
                    output_file = str(rel_output).replace("/", "\\")
                except ValueError:
                    # 手动计算：从 temp 目录 -> ../final/final_output.mp4
                    output_file = "..\\final\\" + output_file_path.name
        
        # 构建ffmpeg命令
        # BorderStyle: 1=无边框(透明背景), 2=只有轮廓, 3=轮廓+阴影
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖输出文件
            "-i", input_video,
            "-vf", f"subtitles={input_subtitle}:force_style='FontName={font},FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)},BorderStyle=1,BackColour=&H{self._bg_color_to_hex(background_color)},{margin}'",
            "-c:a", "copy",
            output_file
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd, cwd=work_dir)
        
        if not success:
            # 如果失败，尝试不使用 force_style
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_video,
                "-vf", f"subtitles={input_subtitle}",
                "-c:a", "copy",
                output_file
            ]
            success, stdout, stderr = FFmpegWrapper.run_command(cmd, cwd=work_dir)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"添加字幕失败: {stderr}"
            )
    
    def add_subtitles_with_ass(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str = None,
        style: Dict[str, Any] = None
    ) -> VideoEditResult:
        """
        使用ASS格式添加字幕（更精细的控制）
        
        Args:
            video_path: 输入视频路径
            subtitle_path: SRT字幕文件路径
            output_path: 输出视频路径
            style: 样式字典
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{video_path}{subtitle_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"subtitled_{hash_str}.mp4")
        
        # 首先转换SRT到ASS
        ass_path = str(Path(subtitle_path).with_suffix('.ass'))
        
        convert_cmd = [
            "ffmpeg",
            "-y",
            "-i", subtitle_path,
            ass_path
        ]
        
        # 设置默认样式
        if style is None:
            style = {
                "FontName": "Arial",
                "FontSize": "24",
                "PrimaryColour": "&H00FFFFFF",
                "BackColour": "&H80000000",
                "Bold": "0",
                "Alignment": "2"  # 底部居中
            }
        
        # 构建样式字符串
        style_str = ",".join([f"{k}={v}" for k, v in style.items()])
        
        # 构建ffmpeg命令
        safe_ass_path = ass_path.replace("\\", "/")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"ass={safe_ass_path}",
            "-c:a", "copy",
            output_path
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"添加字幕失败: {stderr}"
            )
    
    def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str = None,
        audio_offset: float = 0.0
    ) -> VideoEditResult:
        """
        合并音频和视频
        
        Args:
            video_path: 输入视频路径（可能无音频）
            audio_path: 音频文件路径
            output_path: 输出视频路径
            audio_offset: 音频偏移秒数
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if not Path(audio_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"音频文件不存在: {audio_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{video_path}{audio_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"merged_{hash_str}.mp4")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
        if audio_offset != 0:
            cmd.insert(-2, "-itsoffset")
            cmd.insert(-2, str(audio_offset))
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"合并音视频失败: {stderr}"
            )
    
    def add_watermark(
        self,
        video_path: str,
        watermark_path: str,
        output_path: str = None,
        position: str = "bottom-right",
        opacity: float = 0.3
    ) -> VideoEditResult:
        """
        添加水印
        
        Args:
            video_path: 输入视频路径
            watermark_path: 水印图片路径
            output_path: 输出视频路径
            position: 水印位置 (top-left, top-right, bottom-left, bottom-right, center)
            opacity: 透明度 (0-1)
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if not Path(watermark_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"水印文件不存在: {watermark_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(f"{video_path}{watermark_path}".encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"watermarked_{hash_str}.mp4")
        
        # 设置位置
        positions = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2"
        }
        pos = positions.get(position, positions["bottom-right"])
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", watermark_path,
            "-filter_complex", f"[1][0]scale2ref=iw:iw*0.1[wm][vid];[vid][wm]overlay={pos}:format=auto",
            "-c:a", "copy",
            output_path
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"添加水印失败: {stderr}"
            )
    
    def resize_video(
        self,
        video_path: str,
        output_path: str = None,
        width: int = None,
        height: int = None,
        scale: float = None
    ) -> VideoEditResult:
        """
        缩放视频
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            width: 输出宽度
            height: 输出高度
            scale: 缩放比例
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(video_path.encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"resized_{hash_str}.mp4")
        
        if scale:
            vf = f"scale=iw*{scale}:ih*{scale}"
        elif width and height:
            vf = f"scale={width}:{height}"
        elif width:
            vf = f"scale={width}:-2"
        elif height:
            vf = f"scale=-2:{height}"
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg="需要指定scale、width或height"
            )
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:a", "copy",
            output_path
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"缩放视频失败: {stderr}"
            )
    
    def extract_audio(
        self,
        video_path: str,
        output_path: str = None
    ) -> VideoEditResult:
        """
        提取音频
        
        Args:
            video_path: 输入视频路径
            output_path: 输出音频路径
            
        Returns:
            VideoEditResult
        """
        if not Path(video_path).exists():
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"视频文件不存在: {video_path}"
            )
        
        if output_path is None:
            hash_str = hashlib.md5(video_path.encode()).hexdigest()[:8]
            output_dir = OUTPUT_DIR / "audio"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"extracted_{hash_str}.wav")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ]
        
        success, stdout, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            return VideoEditResult(output_path=output_path, success=True)
        else:
            return VideoEditResult(
                output_path="",
                success=False,
                error_msg=f"提取音频失败: {stderr}"
            )
    
    @staticmethod
    def _color_to_hex(color: str) -> str:
        """将颜色名转换为FFmpeg HEX格式 (BGRA)"""
        colors = {
            "white": "FFFFFF",
            "black": "000000",
            "red": "FF0000",
            "green": "00FF00",
            "blue": "0000FF",
            "yellow": "FFFF00",
            "cyan": "00FFFF",
            "magenta": "FF00FF"
        }
        hex_color = colors.get(color.lower(), "FFFFFF")
        # FFmpeg使用ABGR格式
        return f"00{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"
    
    @staticmethod
    def _bg_color_to_hex(color: str) -> str:
        """将背景色转换为FFmpeg HEX格式"""
        # 处理 @0.5 格式的透明度
        if "@" in color:
            color, alpha = color.split("@")
            alpha_val = int(float(alpha) * 255)
        else:
            alpha_val = 128
        
        colors = {
            "black": "000000",
            "white": "FFFFFF",
            "red": "FF0000",
            "green": "00FF00",
            "blue": "0000FF",
            "yellow": "FFFF00"
        }
        hex_color = colors.get(color.lower(), "000000")
        # FFmpeg使用ABGR格式
        return f"{alpha_val:02X}{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"


class VideoPipeline:
    """视频处理流水线"""
    
    def __init__(self):
        self.editor = VideoEditor()
        self.subtitle_generator = SubtitleGenerator()
    
    def create_text_only_video(
        self,
        audio_path: str,
        text: str = None,
        segments: List[Dict[str, Any]] = None,
        output_path: str = None
    ) -> str:
        """
        创建纯文本视频（无人物出镜，仅文字同步显示）
        使用SRT字幕 + subtitles滤镜方案
        
        Args:
            audio_path: 音频路径
            text: 原始文本
            segments: 分段信息
            output_path: 输出视频路径
            
        Returns:
            str: 输出视频路径
        """
        if output_path is None:
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "text_only_output.mp4")
        
        output_file = Path(output_path)
        output_dir_path = output_file.parent.parent
        temp_dir = output_dir_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取音频时长
        duration = 30
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        success, stdout, _ = FFmpegWrapper.run_command(probe_cmd)
        if success and stdout.strip():
            try:
                duration = float(stdout.strip())
            except ValueError:
                pass
        
        # 生成字幕时间戳
        if not segments:
            segments = [{"start": 0.0, "end": duration, "text": text or "Speech"}]
        
        # 视频参数
        width = 1280
        height = 720
        
        # 创建背景视频
        bg_path = str(temp_dir / "text_only_bg.mp4")
        bg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x1a1a2e:s={width}x{height}:d={duration}:rate=25,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            bg_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(bg_cmd)
        if not success:
            raise RuntimeError(f"创建背景视频失败: {stderr}")
        
        print(f"[纯文本视频] 开始生成字幕文件...")
        
        # 生成SRT字幕文件
        srt_path = str(temp_dir / "text_only.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start_time = self._format_srt_time(seg.get("start", 0))
                end_time = self._format_srt_time(seg.get("end", 5))
                seg_text = seg.get("text", "").replace("\n", " ")
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{seg_text}\n\n")
        
        print(f"[纯文本视频] SRT字幕文件已生成")
        
        # 使用subtitles滤镜添加字幕
        # 注意：Windows下路径需要处理
        video_only_path = str(temp_dir / "text_only_video.mp4")
        
        # subtitles滤镜需要在临时目录使用相对路径
        import os
        os.chdir(temp_dir)
        srt_filename = "text_only.srt"
        
        subtitle_cmd = [
            "ffmpeg", "-y",
            "-i", bg_path,
            "-vf", f"subtitles='{srt_filename}':force_style='FontSize=36,PrimaryColour=&H00FFDC32,Alignment=5,MarginV=150'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-an",
            video_only_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(subtitle_cmd)
        
        if not success:
            print(f"[纯文本视频] subtitles方案失败: {stderr[:300]}")
            # 备选：使用drawtext滤镜（单句字幕）
            print(f"[纯文本视频] 尝试备选方案...")
            video_only_path = self._create_text_video_drawtext(bg_path, segments, temp_dir, duration)
        else:
            print(f"[纯文本视频] 字幕添加成功")
        
        print(f"[纯文本视频] 准备合并音频...")
        
        # 合并音频
        final_cmd = [
            "ffmpeg", "-y",
            "-i", video_only_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(final_cmd)
        if not success:
            raise RuntimeError(f"合并音视频失败: {stderr}")
        
        print(f"[纯文本视频] 创建成功: {output_path}")
        return output_path
    
    def _create_text_video_drawtext(
        self,
        bg_path: str,
        segments: List[Dict[str, Any]],
        temp_dir: Path,
        duration: float
    ) -> str:
        """备选方案：使用drawtext滤镜创建字幕"""
        
        # 构建drawtext滤镜 - 简化版，每个时间段显示对应文字
        drawtext_parts = []
        
        for seg in segments:
            seg_text = seg.get("text", "").replace("'", "\\'").replace("\n", " ")
            start = seg.get("start", 0)
            end = seg.get("end", 5)
            
            # 简单绘制文字，居中显示
            filter_str = (
                f"drawtext=text='{seg_text}':"
                f"fontsize=32:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2:"
                f"enable='between(t,{start},{end})':"
                f"fontfile=/Windows/Fonts/arial.ttf"
            )
            drawtext_parts.append(filter_str)
        
        video_only_path = str(temp_dir / "text_only_drawtext.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", bg_path,
            "-vf", ",".join(drawtext_parts),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-an",
            video_only_path
        ]
        
        success, _, stderr = FFmpegWrapper.run_command(cmd)
        
        if success:
            print(f"[纯文本视频] drawtext备选方案成功")
            return video_only_path
        else:
            print(f"[纯文本视频] drawtext备选方案也失败: {stderr[:200]}")
            return bg_path  # 返回无字幕背景
    
    def create_subtitled_video(
        self,
        video_path: str,
        audio_path: str,
        text: str = None,
        word_timings: List[Dict[str, Any]] = None,
        segments: List[Dict[str, Any]] = None,
        output_path: str = None,
        subtitle_style: Dict[str, Any] = None
    ) -> str:
        """
        创建带字幕的视频
        
        Args:
            video_path: 输入视频路径
            audio_path: 音频路径（用于获取时间信息）
            text: 原始文本
            word_timings: 词级时间戳
            segments: 分段信息
            output_path: 输出视频路径
            subtitle_style: 字幕样式
            
        Returns:
            str: 输出视频路径
        """
        if output_path is None:
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "final_output.mp4")
        
        # 使用输出文件的父目录来组织临时文件
        output_file = Path(output_path)
        output_dir_path = output_file.parent.parent  # output/final -> output
        subtitle_dir = output_dir_path / "temp"
        subtitle_dir.mkdir(parents=True, exist_ok=True)
        subtitle_path = str(subtitle_dir / "subtitles.srt")
        
        if word_timings:
            self.subtitle_generator.generate_from_text(text, word_timings, subtitle_path)
        elif segments:
            self.subtitle_generator.generate_from_segments(segments, subtitle_path)
        elif text:
            # 使用Whisper获取时间戳
            from models.tts import WERDetector
            detector = WERDetector()
            try:
                _, segs = detector.transcribe(audio_path)
                # 清理文本
                clean_segs = []
                for seg in segs:
                    clean_segs.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    })
                self.subtitle_generator.generate_from_segments(clean_segs, subtitle_path)
            except Exception as e:
                print(f"获取时间戳失败，使用简单字幕: {e}")
                self.subtitle_generator.generate_from_text(text, [], subtitle_path)
        else:
            raise ValueError("需要提供text、word_timings或segments之一")
        
        # 2. 如果视频没有音频，先合并音频
        video_info = FFmpegWrapper.get_video_info(video_path)
        if not video_info.get("has_audio", False):
            temp_video = str(subtitle_dir / "with_audio.mp4")
            merge_result = self.editor.merge_audio_video(video_path, audio_path, temp_video)
            if merge_result.success:
                video_path = temp_video
        
        # 3. 添加字幕
        # 解析 subtitle_style 字典中的参数
        # 默认样式：字体更小、无阴影、背景透明
        style_kwargs = {
            'font': subtitle_style.get('font', 'Arial') if subtitle_style else 'Arial',
            'font_size': subtitle_style.get('font_size', 18) if subtitle_style else 18,  # 减小字体
            'font_color': subtitle_style.get('color', 'white') if subtitle_style else 'white',
            'background_color': subtitle_style.get('background', 'white@0') if subtitle_style else 'white@0',  # 透明背景
            'position': subtitle_style.get('position', 'bottom') if subtitle_style else 'bottom'
        }
        result = self.editor.add_subtitles(video_path, subtitle_path, output_path, **style_kwargs)
        
        if result.success:
            return result.output_path
        else:
            raise RuntimeError(f"创建字幕视频失败: {result.error_msg}")
    
    def create_split_subtitle_video(
        self,
        video_path: str,
        audio_path: str,
        text: str = None,
        segments: List[Dict[str, Any]] = None,
        output_path: str = None
    ) -> str:
        """
        创建分屏字幕视频（左侧文章+右侧视频，带高亮）
        
        Args:
            video_path: 输入视频路径
            audio_path: 音频路径
            text: 原始文本
            segments: 分段信息
            output_path: 输出视频路径
            
        Returns:
            str: 输出视频路径
        """
        if output_path is None:
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "split_output.mp4")
        
        output_file = Path(output_path)
        output_dir_path = output_file.parent.parent
        temp_dir = output_dir_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取视频信息
        video_info = FFmpegWrapper.get_video_info(video_path)
        video_width = video_info.get("width", 512)
        video_height = video_info.get("height", 512)
        
        # 2. 创建分屏布局视频
        # 左侧（文本区域）：宽度为总宽度的40%
        # 右侧（视频区域）：宽度为总宽度的60%
        total_width = 1280
        total_height = 720
        left_width = int(total_width * 0.4)  # 512
        right_width = int(total_width * 0.6)  # 768
        video_scale_width = right_width
        video_scale_height = total_height
        
        # 调整视频大小以适应右侧区域
        scaled_video_path = str(temp_dir / "scaled_video.mp4")
        scale_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"scale={video_scale_width}:{video_scale_height}:force_original_aspect_ratio=decrease,pad={video_scale_width}:{video_scale_height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            scaled_video_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(scale_cmd)
        if not success:
            raise RuntimeError(f"缩放视频失败: {stderr}")
        
        # 3. 创建分屏视频
        # 使用libavfilter创建左右分屏
        split_video_path = str(temp_dir / "split_video_temp.mp4")
        
        # 创建左侧深灰色背景视频（比黑色更柔和）
        left_video_path = str(temp_dir / "left_video.mp4")
        left_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x1a1a2e:s={left_width}x{total_height}:d={video_info.get('duration', 10)},format=yuv420p",
            left_video_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(left_cmd)
        if not success:
            raise RuntimeError(f"创建左侧视频失败: {stderr}")
        
        # 左侧视频就是黑色背景+文本（暂时跳过ASS字幕，使用hstack直接合并）
        left_with_subtitle_path = left_video_path
        
        # 合并左右视频
        concat_cmd = [
            "ffmpeg", "-y",
            "-i", left_with_subtitle_path,
            "-i", scaled_video_path,
            "-filter_complex", "[0:v][1:v]hstack=inputs=2[out]",
            "-map", "[out]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            split_video_path
        ]
        
        # 尝试使用hstack滤镜
        success, _, stderr = FFmpegWrapper.run_command(concat_cmd)
        if not success:
            # 如果失败，使用xstack滤镜
            print(f"hstack失败，尝试xstack: {stderr}")
            concat_cmd = [
                "ffmpeg", "-y",
                "-i", left_with_subtitle_path,
                "-i", scaled_video_path,
                "-filter_complex", "[0:v][1:v]xstack=inputs=2:layout=0_0|w_H[out]",
                "-map", "[out]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                split_video_path
            ]
            success, _, stderr = FFmpegWrapper.run_command(concat_cmd)
            if not success:
                # 最终降级方案：使用overlay滤镜
                print(f"xstack也失败，尝试overlay方案: {stderr}")
                concat_cmd = [
                    "ffmpeg", "-y",
                    "-i", left_with_subtitle_path,
                    "-i", scaled_video_path,
                    "-filter_complex", "[0:v][1:v]overlay=W:0[out]",
                    "-map", "[out]",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    split_video_path
                ]
                success, _, stderr = FFmpegWrapper.run_command(concat_cmd)
        
        if not success:
            # 如果所有方法都失败，返回原视频
            print(f"分屏创建失败: {stderr}")
            return video_path
        
        # 4. 合并音频
        final_cmd = [
            "ffmpeg", "-y",
            "-i", split_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        success, _, stderr = FFmpegWrapper.run_command(final_cmd)
        
        if not success:
            print(f"合并音频失败: {stderr}")
            return split_video_path
        
        print(f"[分屏模式] 视频创建成功: {output_path}")
        return output_path
    
    def create_text_scrolling_video(
        self,
        audio_path: str,
        text: str = None,
        segments: List[Dict[str, Any]] = None,
        output_path: str = None
    ) -> str:
        """
        创建文本流动视频（仅音频模式）
        使用PIL生成带高亮效果的文本视频帧，然后使用FFmpeg合成
        
        Args:
            audio_path: 音频路径
            text: 原始文本
            segments: 分段信息
            output_path: 输出视频路径
            
        Returns:
            str: 输出视频路径
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("[WARNING] PIL not installed, falling back to audio only")
            return audio_path
        
        if output_path is None:
            output_dir = OUTPUT_DIR / "final"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "text_video_output.mp4")
        
        output_file = Path(output_path)
        output_dir_path = output_file.parent.parent
        frames_dir = output_dir_path / "text_video_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取音频时长
        audio_info = FFmpegWrapper.get_video_info(audio_path)
        duration = audio_info.get("duration", 10)
        
        # 视频参数
        fps = 10  # 使用较低的帧率以加快处理速度
        width, height = 720, 960
        total_frames = int(duration * fps)
        
        print(f"[文本流动视频] 生成 {total_frames} 帧...")
        
        # 加载字体
        try:
            font_size = 32
            font = ImageFont.truetype("arial.ttf", font_size)
            small_font = ImageFont.truetype("arial.ttf", 26)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 生成帧
        for frame_idx in range(total_frames):
            current_time = frame_idx / fps
            
            # 找到当前播放的句子
            current_segment_idx = 0
            for i, seg in enumerate(segments or []):
                if seg.get("start", 0) <= current_time < seg.get("end", 0):
                    current_segment_idx = i
                    break
            
            # 创建黑色背景
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            
            # 绘制文本行
            line_height = 50
            base_y = 100
            padding = 40
            
            for i, seg in enumerate(segments or []):
                if i < len(segments or []):
                    # 确定文本颜色
                    if i == current_segment_idx:
                        text_color = (0, 255, 0)  # 绿色高亮
                        current_font = font
                    else:
                        text_color = (100, 100, 100)  # 灰色
                        current_font = small_font
                    
                    # 绘制文本（处理换行）
                    y_pos = base_y + i * line_height
                    # 简单处理：如果文本太长，截断
                    text = seg.get("text", "")[:50]
                    draw.text((padding, y_pos), text, font=current_font, fill=text_color)
            
            # 保存帧
            frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
            img.save(frame_path)
            
            if (frame_idx + 1) % 100 == 0:
                print(f"  进度: {frame_idx + 1}/{total_frames} 帧")
        
        print(f"[文本流动视频] 帧生成完成")
        
        # 使用FFmpeg将帧合成为视频
        print(f"[文本流动视频] 合成视频...")
        temp_video_path = str(output_dir_path / "temp" / "text_video_no_audio.mp4")
        Path(temp_video_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            temp_video_path
        ]
        
        success, _, stderr = FFmpegWrapper.run_command(cmd)
        if not success:
            print(f"[ERROR] 视频合成失败: {stderr}")
            # 清理临时文件
            import shutil
            shutil.rmtree(frames_dir, ignore_errors=True)
            return audio_path
        
        # 合并音频
        print(f"[文本流动视频] 合并音频...")
        final_cmd = [
            "ffmpeg", "-y",
            "-i", temp_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        
        success, _, stderr = FFmpegWrapper.run_command(final_cmd)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(frames_dir, ignore_errors=True)
        Path(temp_video_path).unlink(missing_ok=True)
        
        if success:
            print(f"[文本流动视频] 创建成功: {output_path}")
            return output_path
        else:
            print(f"[ERROR] 音频合并失败: {stderr}")
            return audio_path
