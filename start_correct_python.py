import subprocess
import sys
import time

python_path = r"C:\Users\ASUS\AppData\Local\Programs\Python\Python314\python.exe"

print("=" * 60)
print(f"Starting Flask with Python 3.14...")
print(f"Python path: {python_path}")
print("=" * 60)

# Start server
proc = subprocess.Popen(
    [python_path, "server.py"],
    cwd=r"D:\_BiShe\demo_1",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

print("Waiting for server to start...")
time.sleep(6)

print("\nServer should be running. Check with:")
print("  http://localhost:5000")
print("\nPress Ctrl+C to stop server")

# Keep process running
try:
    for line in proc.stdout:
        print(line.rstrip())
except KeyboardInterrupt:
    print("\nStopping server...")
    proc.terminate()
    proc.wait()
    print("Server stopped")
