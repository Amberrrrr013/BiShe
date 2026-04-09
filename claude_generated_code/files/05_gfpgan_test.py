# ============================================================
# 模块：GFPGAN 人脸超分辨率修复
# 环境：D:\_BiShe\gfpgan\env
# 依赖：
#   pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
#   pip install gfpgan realesrgan
#   pip install numpy==1.26.4  # 必须锁定，不能用2.x
#
# 模型文件（放在 D:\_BiShe\gfpgan\ 根目录）：
#   GFPGANv1.4.pth（约340MB）
#   下载：Invoke-WebRequest -Uri "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" -OutFile "GFPGANv1.4.pth"
#
# 注意：GFPGAN 只支持图片输入，不支持直接处理视频
# 输出图片位置：输出目录下的 restored_imgs\ 子文件夹
# ============================================================

# GFPGAN 通过命令行运行，在 D:\_BiShe\gfpgan\ 目录下执行：

# 处理单张图片：
# python inference_gfpgan.py -i "输入图片.jpg" -o "输出目录" -v 1.4 -s 2
# 参数说明：
#   -v 1.4  使用 GFPGANv1.4 模型
#   -s 2    放大倍数（1=原尺寸修复，2=放大2倍）

# 实际测试命令：
# python inference_gfpgan.py -i "D:\_BiShe\talking-head_test\wang_zhong_head.jpg" -o "D:\_BiShe\talking-head_test" -v 1.4 -s 2

# ============================================================
# 在 Python 中通过 subprocess 调用 GFPGAN（用于 Agent 集成）
# ============================================================
import subprocess
import os

def run_gfpgan(input_path: str, output_dir: str, scale: int = 2) -> str:
    """
    调用 GFPGAN 进行人脸修复与超分辨率
    
    Args:
        input_path: 输入图片路径
        output_dir: 输出目录（修复后图片在 output_dir/restored_imgs/ 下）
        scale: 放大倍数，默认2
    
    Returns:
        修复后图片的路径
    """
    gfpgan_dir = r"D:\_BiShe\gfpgan"
    python_exe = r"D:\_BiShe\gfpgan\env\Scripts\python.exe"
    script = os.path.join(gfpgan_dir, "inference_gfpgan.py")

    cmd = [
        python_exe, script,
        "-i", input_path,
        "-o", output_dir,
        "-v", "1.4",
        "-s", str(scale)
    ]

    result = subprocess.run(cmd, cwd=gfpgan_dir, capture_output=True, text=True)

    if result.returncode == 0:
        # 修复后的图片在 restored_imgs 子目录下，文件名不变
        filename = os.path.basename(input_path)
        restored_path = os.path.join(output_dir, "restored_imgs", filename)
        print(f"GFPGAN 修复成功：{restored_path}")
        return restored_path
    else:
        print(f"GFPGAN 错误：{result.stderr}")
        return input_path  # 失败时返回原路径


# 测试调用
if __name__ == "__main__":
    restored = run_gfpgan(
        input_path=r"D:\_BiShe\talking-head_test\wang_zhong_head.jpg",
        output_dir=r"D:\_BiShe\talking-head_test"
    )
    print(f"修复后图片：{restored}")
