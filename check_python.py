import sys
import os

print("Python Environment Info")
print("=" * 60)
print(f"Executable: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Path: {sys.path[:3]}")

print("\nChecking langchain_openai...")
try:
    import langchain_openai
    print(f"FOUND: {langchain_openai.__file__}")
except ImportError as e:
    print(f"NOT FOUND: {e}")

print("\n" + "=" * 60)
