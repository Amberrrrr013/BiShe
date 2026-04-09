# ============================================================
# 模块：SadTalker 说话人视频生成（带头部运动）
# 环境：D:\_BiShe\sadtalker\env
# 依赖：
#   pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
#   pip install -r requirements.txt
#   pip install numpy==1.26.4  # 必须在装完requirements.txt后执行
#
# 模型文件（放在 checkpoints\ 目录）：
#   mapping_00109-model.pth.tar
#   mapping_00229-model.pth.tar
#   SadTalker_V0.0.2_256.safetensors
#   SadTalker_V0.0.2_512.safetensors
#
# 人脸相关模型（放在 gfpgan\weights\ 目录）：
#   detection_Resnet50_Final.pth
#   parsing_parsenet.pth
#
# 特点：
#   - 支持从单张图片生成带头部运动的说话视频
#   - 比 Wav2Lip 画质更好，但速度更慢（2分钟视频约17分钟）
#   - 3060 6GB 可以运行
# ============================================================

# SadTalker 通过命令行运行，在 D:\_BiShe\sadtalker\ 目录下执行：

# 基础用法：
# python inference.py \
#     --driven_audio "音频.wav" \
#     --source_image "人脸图片.jpg" \
#     --result_dir "输出目录" \
#     --still \          # 减少头部运动幅度，更自然
#     --preprocess crop  # 自动裁剪人脸区域

# 实际测试命令：
# python inference.py --driven_audio "D:\_BiShe\whisper_test\test_1.wav" --source_image "D:\_BiShe\talking-head_test\wang_zhong_head.jpg" --result_dir "D:\_BiShe\talking-head_test" --still --preprocess crop

# 输出：result_dir 下会生成以时间戳命名的 mp4 文件

# ============================================================
# 在 Python 中通过 subprocess 调用 SadTalker（用于 Agent 集成）
# ============================================================
import subprocess
import os
import glob

def run_sadtalker(audio_path: str, image_path: str, output_dir: str) -> str:
    """
    调用 SadTalker 生成说话人视频
    
    Args:
        audio_path: 驱动音频路径（.wav）
        image_path: 人脸图片路径
        output_dir: 输出目录
    
    Returns:
        生成的视频路径
    """
    sadtalker_dir = r"D:\_BiShe\sadtalker"
    python_exe = r"D:\_BiShe\sadtalker\env\Scripts\python.exe"
    script = os.path.join(sadtalker_dir, "inference.py")

    cmd = [
        python_exe, script,
        "--driven_audio", audio_path,
        "--source_image", image_path,
        "--result_dir", output_dir,
        "--still",
        "--preprocess", "crop"
    ]

    result = subprocess.run(cmd, cwd=sadtalker_dir, capture_output=True, text=True)

    if result.returncode == 0:
        # 找到最新生成的 mp4 文件
        mp4_files = glob.glob(os.path.join(output_dir, "*.mp4"))
        if mp4_files:
            latest = max(mp4_files, key=os.path.getmtime)
            print(f"SadTalker 生成成功：{latest}")
            return latest
    else:
        print(f"SadTalker 错误：{result.stderr}")

    return ""


# 测试调用
if __name__ == "__main__":
    video = run_sadtalker(
        audio_path=r"D:\_BiShe\whisper_test\test_1.wav",
        image_path=r"D:\_BiShe\talking-head_test\wang_zhong_head.jpg",
        output_dir=r"D:\_BiShe\talking-head_test"
    )
    print(f"输出视频：{video}")
