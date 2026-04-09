import subprocess
import sys
import os

print("Starting Flask Server with Debug...")
print("=" * 60)
print(f"Python: {sys.executable}")

# Check if flask can import
try:
    import flask
    print(f"Flask: {flask.__file__}")
except ImportError:
    print("Flask not found!")

try:
    import langchain_openai
    print(f"langchain_openai: {langchain_openai.__file__}")
except ImportError:
    print("langchain_openai not found!")

print("\nStarting server...")

# Run with error output
result = subprocess.run(
    [sys.executable, "server.py"],
    cwd="D:\_BiShe\demo_1",
    capture_output=True,
    text=True,
    timeout=10
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)
