这是个很有意思的项目！核心思路是：用 Python 处理文本对齐（把音频时间戳和句子对上），然后用 `ffmpeg` 将文章渲染成视频，逐句高亮。

整体流程分三步：---

## 两种方案详解

### 方案一：Python 渲染帧 + ffmpeg 合成（推荐，中文友好）

**第一步：获取时间戳**

用 [WhisperX](https://github.com/m-bain/whisperX) 对音频做对齐，得到每句的 `start` / `end` 时间：

```bash
pip install whisperx
```

```python
import whisperx

model = whisperx.load_model("base", device="cpu")
result = model.transcribe("audio.mp3")
# result["segments"] 里每个元素有 start, end, text
```

如果你的文章文本是**固定已知**的（不是 Whisper 转录的），可以用 `whisperx.align()` 把 Whisper 的词时间戳对齐到你自己的文本上。

**第二步：渲染逐帧图片**

```python
from PIL import Image, ImageDraw, ImageFont
import os, textwrap

sentences = [
    {"text": "This is the first sentence.", "start": 0.0, "end": 2.5},
    {"text": "Here comes the second one.", "start": 2.5, "end": 5.0},
    # ...
]

FPS = 25
W, H = 1280, 720
font_normal = ImageFont.truetype("NotoSansSC-Regular.ttf", 32)
font_highlight = ImageFont.truetype("NotoSansSC-Bold.ttf", 36)

os.makedirs("frames", exist_ok=True)

# 计算总帧数（根据音频时长）
total_duration = 60.0  # 秒，按你的音频时长填
total_frames = int(total_duration * FPS)

def get_current_sentence(t):
    for i, s in enumerate(sentences):
        if s["start"] <= t < s["end"]:
            return i
    return -1

for frame_idx in range(total_frames):
    t = frame_idx / FPS
    active = get_current_sentence(t)
    
    img = Image.new("RGB", (W, H), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    y = 80
    for i, s in enumerate(sentences):
        color = (255, 220, 50) if i == active else (200, 200, 200)
        font = font_highlight if i == active else font_normal
        # 换行处理
        lines = textwrap.wrap(s["text"], width=50)
        for line in lines:
            draw.text((80, y), line, font=font, fill=color)
            y += 45
        y += 10
    
    img.save(f"frames/frame_{frame_idx:06d}.png")
```

**第三步：ffmpeg 合成**

```bash
ffmpeg -framerate 25 -i frames/frame_%06d.png \
       -i audio.mp3 \
       -c:v libx264 -pix_fmt yuv420p \
       -c:a aac -shortest \
       output.mp4
```

***

### 方案二：纯 ffmpeg（英文 / 简单场景）

如果句子少、文字不复杂，可以用 `ffmpeg` 的 `drawtext` filter，通过 `enable='between(t,start,end)'` 控制每句的显示时段：

```bash
ffmpeg -f lavfi -i color=c=black:s=1280x720:r=25 \
       -i audio.mp3 \
       -filter_complex "
         [0:v]drawtext=text='First sentence':
           fontfile=/path/to/font.ttf:fontsize=48:
           fontcolor=yellow:x=80:y=100:
           enable='between(t,0,2.5)',
         drawtext=text='Second sentence':
           fontfile=/path/to/font.ttf:fontsize=48:
           fontcolor=white:x=80:y=160:
           enable='between(t,2.5,5.0)'
         [v]" \
       -map "[v]" -map 1:a \
       -c:v libx264 -c:a aac -shortest output.mp4
```

缺点：句子一多，filter\_complex 会很长；中文字体路径要正确指定；不支持自动换行。

***

## 推荐路线

| 场景           | 推荐方案                 |
| ------------ | -------------------- |
| 中文文章、多句、排版灵活 | 方案一（Pillow + ffmpeg） |
| 英文、句子少、快速验证  | 方案二（纯 ffmpeg）        |
| 需要精确对齐不确定时间戳 | 先用 WhisperX 对齐       |

