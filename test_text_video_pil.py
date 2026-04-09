"""
Test text scrolling video functionality using PIL
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageDraw, ImageFont
import subprocess

def create_text_video_with_pil():
    """Create text video using PIL"""
    print("=" * 50)
    print("Testing Text Scrolling Video with PIL")
    print("=" * 50)
    
    # Test parameters
    test_text = "Hello world. This is a test. English speech synthesis. Digital human video."
    test_segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello world."},
        {"start": 2.0, "end": 4.5, "text": "This is a test."},
        {"start": 4.5, "end": 7.5, "text": "English speech synthesis."},
        {"start": 7.5, "end": 10.0, "text": "Digital human video."}
    ]
    
    output_dir = Path("d:/_BiShe/demo_1/output/test_text_video")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Video parameters
    duration = test_segments[-1]["end"] + 1.0
    fps = 30
    width, height = 720, 960
    total_frames = int(duration * fps)
    
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    print(f"\n[Step 1] Creating {total_frames} frames...")
    
    # Create font (use default, will fall back to system font)
    try:
        font_size = 36
        font = ImageFont.truetype("arial.ttf", font_size)
        small_font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Generate frames
    for frame_idx in range(total_frames):
        current_time = frame_idx / fps
        
        # Find current segment
        current_segment_idx = 0
        for i, seg in enumerate(test_segments):
            if seg["start"] <= current_time < seg["end"]:
                current_segment_idx = i
                break
        
        # Create black background
        img = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Draw all text segments
        line_height = 50
        base_y = 100
        
        for i, seg in enumerate(test_segments):
            if i < len(test_segments):
                # Determine text color
                if i == current_segment_idx:
                    # Highlighted (green)
                    text_color = (0, 255, 0)  # Green
                    current_font = font
                else:
                    # Dimmed (gray)
                    text_color = (128, 128, 128)  # Gray
                    current_font = small_font
                
                # Draw text
                y_pos = base_y + i * line_height
                draw.text((50, y_pos), seg["text"], font=current_font, fill=text_color)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_path)
        
        if (frame_idx + 1) % 100 == 0:
            print(f"  Progress: {frame_idx + 1}/{total_frames} frames")
    
    print(f"[OK] Created {total_frames} frames")
    
    # Create video from frames using FFmpeg
    print("\n[Step 2] Creating video from frames...")
    video_path = str(output_dir / "text_video_pil.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] Video created: {video_path}")
    else:
        print(f"[FAIL] Video creation failed: {result.stderr}")
        return
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print(f"Output file: {video_path}")
    print("=" * 50)

if __name__ == "__main__":
    create_text_video_with_pil()
