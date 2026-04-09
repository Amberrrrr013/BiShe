# ============================================================
# 模块：Wav2Lip 唇形同步视频生成
# 环境：D:\_BiShe\wav2lip\env
# 依赖：
#   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
#   pip install numpy==1.23.5 opencv-python opencv-contrib-python librosa==0.9.2 tqdm
# 
# 模型文件（放在 checkpoints\ 目录下）：
#   wav2lip_gan.pth（约430MB）
#   下载：Invoke-WebRequest -Uri "https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip_gan.pth" -OutFile "checkpoints\wav2lip_gan.pth"
#
# 人脸检测模型（放在 face_detection\detection\sfd\ 目录下）：
#   s3fd.pth（约85MB）
#   下载：Invoke-WebRequest -Uri "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth" -OutFile "face_detection\detection\sfd\s3fd.pth"
#
# 使用方式：命令行调用 inference.py（不是 Python 脚本直接导入）
# ============================================================

# Wav2Lip 通过命令行运行，以下是调用示例
# 在 D:\_BiShe\wav2lip\ 目录下激活 env 后执行：

# 基础用法（图片输入）：
# python inference.py \
#     --checkpoint_path checkpoints\wav2lip_gan.pth \
#     --face "你的人脸图片.jpg" \
#     --audio "你的音频.wav" \
#     --outfile "输出视频.mp4"

# 实际测试命令：
# python inference.py --checkpoint_path checkpoints\wav2lip_gan.pth --face "D:\_BiShe\talking-head_test\wang_zhong_head.jpg" --audio "D:\_BiShe\whisper_test\test_1.wav" --outfile "D:\_BiShe\talking-head_test\result.mp4"

# 如果要用修复后的高清图片（GFPGAN处理后）：
# python inference.py --checkpoint_path checkpoints\wav2lip_gan.pth --face "D:\_BiShe\talking-head_test\restored_imgs\wang_zhong_head.jpg" --audio "D:\_BiShe\whisper_test\test_1.wav" --outfile "D:\_BiShe\talking-head_test\result_enhanced.mp4"

# ============================================================
# 在 Python 中通过 subprocess 调用 Wav2Lip（用于 Agent 集成）
# ============================================================
import subprocess
import os

def run_wav2lip(face_path: str, audio_path: str, output_path: str):
    """
    调用 Wav2Lip 生成唇形同步视频
    
    Args:
        face_path: 人脸图片或视频路径
        audio_path: 驱动音频路径（.wav）
        output_path: 输出视频路径（.mp4）
    """
    wav2lip_dir = r"D:\_BiShe\wav2lip"
    python_exe = r"D:\_BiShe\wav2lip\env\Scripts\python.exe"
    inference_script = os.path.join(wav2lip_dir, "inference.py")
    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")

    cmd = [
        python_exe, inference_script,
        "--checkpoint_path", checkpoint,
        "--face", face_path,
        "--audio", audio_path,
        "--outfile", output_path
    ]

    result = subprocess.run(cmd, cwd=wav2lip_dir, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Wav2Lip 生成成功：{output_path}")
    else:
        print(f"Wav2Lip 错误：{result.stderr}")

    return result.returncode == 0


# 测试调用
if __name__ == "__main__":
    run_wav2lip(
        face_path=r"D:\_BiShe\talking-head_test\wang_zhong_head.jpg",
        audio_path=r"D:\_BiShe\whisper_test\test_1.wav",
        output_path=r"D:\_BiShe\talking-head_test\result.mp4"
    )
