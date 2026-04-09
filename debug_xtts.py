from models.tts import XTTSTTSProvider
import subprocess
import re

ref_wav = r'D:\_BiShe\demo_1\output\temp\recordings\recorded_audio_2026.04.03_14.22.20_9c7854ce.wav'
output_path = r'D:/test_debug.wav'
text = 'Hello test.'

provider = XTTSTTSProvider()
xtts_base = provider.model_path
from pathlib import Path
xtts_site_packages = Path(xtts_base) / 'env' / 'Lib' / 'site-packages'

script = f'''
import sys
sys.path.insert(0, r"{xtts_site_packages}")
from TTS.api import TTS
import librosa
import torch

print("XTTS进度: 正在加载模型...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.to("cuda")
print("XTTS进度: 模型加载完成")

ref_duration = librosa.get_duration(path={repr(ref_wav)})
print(f"XTTS进度: 参考音频时长 {{ref_duration:.1f}} 秒")

tts.tts_to_file(
    text={repr(text)},
    speaker_wav={repr(ref_wav)},
    language="en",
    file_path={repr(output_path)}
)
print("XTTS进度: 语音合成完成...")

duration = librosa.get_duration(path={repr(output_path)})
print(f"XTTS完成: 生成的音频时长 {{duration:.1f}} 秒")
'''

result = subprocess.run(
    [provider._python_exe, '-c', script],
    capture_output=True,
    text=True,
    timeout=900
)

print('Return code:', result.returncode)
print('\n--- STDOUT ---')
print(result.stdout)
print('\n--- STDERR (first 500) ---')
print(result.stderr[:500] if result.stderr else 'None')

# Test parsing
print('\n--- Parsing Test ---')
duration = 0.0
for line in result.stdout.strip().split('\n'):
    line = line.strip()
    if not line:
        continue
    match = re.search(r'生成的音频时长\s*(\d+\.?\d*)\s*秒', line)
    if match:
        duration = float(match.group(1))
        print(f'Found duration: {duration}')
        break
else:
    print('No match found!')
    print('Trying simple float parse on lines:')
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if line:
            print(f'  Line: {repr(line)}')
