import subprocess
import sys
import time
import requests

print("Starting server and capturing all output...")

# Start server
proc = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd="D:\_BiShe\demo_1",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for server to start
print("Waiting for server startup...")
time.sleep(5)

print("Server started. Making request...")

try:
    response = requests.post(
        "http://127.0.0.1:5000/api/agent/chat",
        json={
            "message": "帮我制作一个关于气候变化的英语演讲视频",
            "history": [],
            "auto_execute": False
        },
        timeout=60
    )
    print(f"\nRequest completed with status: {response.status_code}")
    print(f"Response length: {len(response.text)}")
    
except Exception as e:
    print(f"\nRequest failed: {e}")

print("\nServer output:")
print("=" * 60)

# Read output until process ends or timeout
import select

try:
    while True:
        # Check if there's output ready
        if proc.stdout in select.select([proc.stdout], [], [], 0.5)[0]:
            line = proc.stdout.readline()
            if line:
                print(line.rstrip())
            else:
                break
        else:
            # No output, check if process is still running
            if proc.poll() is not None:
                break
except KeyboardInterrupt:
    print("\nInterrupted")
finally:
    proc.terminate()
    proc.wait()
    print("\nServer stopped")
