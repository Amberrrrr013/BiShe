"""
测试分屏模式修复
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.video_editor import VideoPipeline

def test_split_video():
    """测试分屏模式"""
    print("=" * 60)
    print("测试分屏模式修复")
    print("=" * 60)
    
    # 使用现有的测试视频
    video_path = r"D:\_BiShe\demo_1\output\non_agent\2026.04.03_16.11.58\video\wav2lip_07c1a79a_0.mp4"
    audio_path = r"D:\_BiShe\demo_1\output\non_agent\2026.04.03_16.11.58\audio\speech.wav"
    output_dir = r"D:\_BiShe\demo_1\output\test_split"
    
    # 检查文件是否存在
    if not Path(video_path).exists():
        print(f"[ERROR] 视频文件不存在: {video_path}")
        # 尝试找其他视频
        videos = list(Path(r"D:\_BiShe\demo_1\output").rglob("wav2lip_*.mp4"))
        if videos:
            video_path = str(videos[0])
            print(f"[INFO] 使用替代视频: {video_path}")
        else:
            print("[ERROR] 没有找到可用的测试视频")
            return
    
    if not Path(audio_path).exists():
        print(f"[WARNING] 音频文件不存在: {audio_path}")
        # 尝试找其他音频
        audios = list(Path(r"D:\_BiShe\demo_1\output").rglob("*.wav"))
        if audios:
            audio_path = str(audios[0])
            print(f"[INFO] 使用替代音频: {audio_path}")
    
    print(f"[INFO] 视频: {video_path}")
    print(f"[INFO] 音频: {audio_path}")
    
    # 测试文本
    test_text = """
    Good morning, everyone. Today I want to share with you an exciting topic: 
    the future of artificial intelligence in education. As we all know, 
    technology is rapidly changing the way we learn and teach. 
    AI has the potential to personalize learning experiences 
    and make education more accessible to everyone.
    """
    
    # 分段信息
    segments = [
        {"start": 0.0, "end": 5.0, "text": "Good morning, everyone."},
        {"start": 5.0, "end": 10.0, "text": "Today I want to share with you an exciting topic:"},
        {"start": 10.0, "end": 15.0, "text": "the future of artificial intelligence in education."},
        {"start": 15.0, "end": 20.0, "text": "As we all know, technology is rapidly changing the way we learn and teach."},
        {"start": 20.0, "end": 25.0, "text": "AI has the potential to personalize learning experiences."},
        {"start": 25.0, "end": 30.0, "text": "and make education more accessible to everyone."},
    ]
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = str(Path(output_dir) / "split_test_output.mp4")
    
    print(f"\n[Step 1] 开始测试分屏模式...")
    print(f"[Step 2] 输出路径: {output_path}")
    
    try:
        pipeline = VideoPipeline()
        result_path = pipeline.create_split_subtitle_video(
            video_path=video_path,
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
    result = test_split_video()
    if result:
        print(f"\n测试视频已生成: {result}")
