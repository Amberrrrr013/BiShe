"""
测试纯文本视频生成
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.video_editor import VideoPipeline

def test_text_video():
    """测试纯文本视频"""
    print("=" * 60)
    print("测试纯文本视频生成")
    print("=" * 60)
    
    # 查找测试音频
    audio_path = None
    for audio in Path(r"D:\_BiShe\demo_1\output").rglob("*.wav"):
        audio_path = str(audio)
        break
    
    if not audio_path:
        print("[ERROR] 没有找到测试音频文件")
        return
    
    print(f"[INFO] 使用音频: {audio_path}")
    
    # 测试文本
    test_text = """Good morning, everyone.
Today I want to share with you an exciting topic about artificial intelligence.
AI is changing the way we live and work.
It has tremendous potential to improve our daily lives.
Thank you for listening."""
    
    # 分段信息
    segments = [
        {"start": 0.0, "end": 3.0, "text": "Good morning, everyone."},
        {"start": 3.0, "end": 7.0, "text": "Today I want to share with you an exciting topic about artificial intelligence."},
        {"start": 7.0, "end": 11.0, "text": "AI is changing the way we live and work."},
        {"start": 11.0, "end": 15.0, "text": "It has tremendous potential to improve our daily lives."},
        {"start": 15.0, "end": 18.0, "text": "Thank you for listening."},
    ]
    
    output_path = r"D:\_BiShe\demo_1\output\test_split\text_only_output.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[Step 1] 开始生成纯文本视频...")
    print(f"[Step 2] 输出路径: {output_path}")
    
    try:
        pipeline = VideoPipeline()
        result_path = pipeline.create_text_only_video(
            audio_path=audio_path,
            text=test_text,
            segments=segments,
            output_path=output_path
        )
        
        print("\n" + "=" * 60)
        print(f"[SUCCESS] 测试完成!")
        print(f"[SUCCESS] 输出文件: {result_path}")
        print("=" * 60)
        
        return result_path
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_text_video()
    if result:
        print(f"\n纯文本视频已生成: {result}")
